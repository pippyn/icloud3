"""
Platform that supports scanning iCloud.
For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.icloud/


Notes:
1. Changes to the icloud device_tracker were first inspired by icloud2.py
   developed by Walt Howd.
    -

.

"""

#pylint: disable=bad-continuation, import-error, invalid-name, bare-except
#pylint: disable=too-many-arguments, too-many-statements, too-many-branches
#pylint: disable=too-many-locals, too-many-return-statements
#pylint: disable=unused-argument, unused-variable
#pylint: disable=too-many-instance-attributes, too-many-lines

import logging
import os
import time
import voluptuous as vol

from   homeassistant.const                import CONF_USERNAME, CONF_PASSWORD
from   homeassistant.components.device_tracker import (
          PLATFORM_SCHEMA, DOMAIN, ATTR_ATTRIBUTES, DeviceScanner)
from   homeassistant.components.zone.zone import active_zone
from   homeassistant.helpers.event        import track_utc_time_change
import homeassistant.helpers.config_validation as cv
from   homeassistant.util                 import slugify
import homeassistant.util.dt              as dt_util
from   homeassistant.util.location        import distance
import WazeRouteCalculator


_LOGGER = logging.getLogger(__name__)

REQUIREMENTS = ['pyicloud==0.9.1']

CONF_ACCOUNTNAME            = 'account_name'
CONF_INCLUDE_DEVICETYPES    = 'include_device_types'
CONF_EXCLUDE_DEVICETYPES    = 'exclude_device_types'
CONF_INCLUDE_DEVICES        = 'include_devices'
CONF_EXCLUDE_DEVICES        = 'exclude_devices'
CONF_INCLUDE_DEVICETYPE     = 'include_device_type'
CONF_EXCLUDE_DEVICETYPE     = 'exclude_device_type'
CONF_INCLUDE_DEVICE         = 'include_device'
CONF_EXCLUDE_DEVICE         = 'exclude_device'
CONF_DEVICENAME             = 'device_name'
CONF_UNIT_OF_MEASUREMENT    = 'unit_of_measurement'
CONF_INTERVAL               = 'interval'
CONF_INZONE_INTERVAL        = 'inzone_interval'
CONF_MAX_INTERVAL           = 'max_interval'
CONF_TRAVEL_TIME_FACTOR     = 'travel_time_factor'
CONF_GPS_ACCURACY_THRESHOLD = 'gps_accuracy_threshold'
CONF_WAZE_REGION            = 'waze_region'
CONF_WAZE_MAX_DISTANCE      = 'waze_max_distance'
CONF_WAZE_MIN_DISTANCE      = 'waze_min_distance'
CONF_WAZE_REALTIME          = 'waze_realtime'
CONF_DISTANCE_METHOD        = 'distance_method'
CONF_COMMAND                = 'command'

# entity attributes
ATTR_BATTERY             = 'battery'
ATTR_DISTANCE            = 'distance'
ATTR_CALC_DISTANCE       = 'calc_distance'
ATTR_WAZE_DISTANCE       = 'waze_distance'
ATTR_WAZE_TIME           = 'travel_time'
ATTR_DIR_OF_TRAVEL       = 'dir_of_travel'
ATTR_DEVICESTATUS        = 'device_status'
ATTR_LOWPOWERMODE        = 'low_power_mode'
ATTR_BATTERYSTATUS       = 'battery_status'
ATTR_TRACKED_DEVICES     = 'tracked_devices'
ATTR_LAST_UPDATE_TIME    = 'last_update'
ATTR_NEXT_UPDATE_TIME    = 'next_update'
ATTR_LAST_LOCATED        = 'last_located'
ATTR_INFO                = 'info'
ATTR_GPS_ACCURACY        = 'gps_accuracy'
ATTR_LATITUDE            = 'latitude'
ATTR_LONGITUDE           = 'longitude'
ATTR_POLL_COUNT          = 'poll_count'

#icloud_update commands
CMD_ERROR    = 1
CMD_INTERVAL = 2
CMD_PAUSE    = 3
CMD_RESUME   = 4
CMD_WAZE     = 5

#Waze status codes
WAZE_REGIONS      = ['US', 'NA', 'EU', 'IL']
WAZE_USED         = 0
WAZE_NOT_USED     = 1
WAZE_PAUSED       = 2
WAZE_OUT_OF_RANGE = 3
WAZE_ERROR        = 4

# If the location data is old during the _update_all_devices routine,
# it will retry polling the device (or all devices) after 3 seconds,
# up to 4 times. If the data is still old, it will set the next normal
# interval to C_LOCATION_ISOLD_INTERVAL and keep track of the number of
# times it overrides the normal polling interval. If it is still old after
# C_MAX_LOCATION_ISOLD_CNT retries, the normal intervl will be used and
# the cycle starts over on the next poll. This will prevent a constant
# repolling if the location data is always old.
C_LOCATION_ISOLD_INTERVAL = 15
C_MAX_LOCATION_ISOLD_CNT = 4


ICLOUDTRACKERS = {}

_CONFIGURING = {}

DEVICESTATUSSET = ['deviceModel', 'rawDeviceModel', 'deviceStatus',
                    'deviceClass', 'batteryLevel', 'id', 'lowPowerMode',
                    'deviceDisplayName', 'name', 'batteryStatus', 'fmlyShare',
                    'location',
                    'locationCapable', 'locationEnabled', 'isLocating',
                    'remoteLock', 'activationLocked', 'lockedTimestamp',
                    'lostModeCapable', 'lostModeEnabled', 'locFoundEnabled',
                    'lostDevice', 'lostTimestamp',
                    'remoteWipe', 'wipeInProgress', 'wipedTimestamp',
                    'isMac']

DEVICESTATUSCODES = {
    '200': 'online',
    '201': 'offline',
    '203': 'pending',
    '204': 'unregistered',
}

SERVICE_SCHEMA = vol.Schema({
    vol.Optional(CONF_ACCOUNTNAME): vol.All(cv.ensure_list, [cv.slugify]),
    vol.Optional(CONF_DEVICENAME): cv.slugify,
    vol.Optional(CONF_INTERVAL): cv.slugify,
    vol.Optional(CONF_COMMAND): cv.string
})

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_ACCOUNTNAME): cv.slugify,
    #-----??General Attributes ----------
    vol.Optional(CONF_UNIT_OF_MEASUREMENT, default='km'): cv.slugify,
    vol.Optional(CONF_INZONE_INTERVAL, default='1 hr'): cv.string,
    vol.Optional(CONF_MAX_INTERVAL, default=0): cv.string,
    vol.Optional(CONF_TRAVEL_TIME_FACTOR, default=.75): cv.string,
    vol.Optional(CONF_GPS_ACCURACY_THRESHOLD, default=100): cv.string,
    vol.Optional(ATTR_GPS_ACCURACY): cv.slugify,
    #-----??Filter, Include, Exclude Devices ----------
    vol.Optional(CONF_INCLUDE_DEVICETYPES): cv.string,
    vol.Optional(CONF_INCLUDE_DEVICETYPE): cv.string,
    vol.Optional(CONF_INCLUDE_DEVICES): cv.string,
    vol.Optional(CONF_INCLUDE_DEVICE): cv.string,
    vol.Optional(CONF_EXCLUDE_DEVICETYPES): cv.string,
    vol.Optional(CONF_EXCLUDE_DEVICETYPE): cv.string,
    vol.Optional(CONF_EXCLUDE_DEVICES): cv.string,
    vol.Optional(CONF_EXCLUDE_DEVICE): cv.string,
    vol.Optional(ATTR_TRACKED_DEVICES): cv.string,
    #-----??Location Attributes  ----------
    vol.Optional(ATTR_LAST_UPDATE_TIME): cv.slugify,
    vol.Optional(ATTR_NEXT_UPDATE_TIME): cv.slugify,
    vol.Optional(ATTR_LAST_LOCATED): cv.slugify,
    vol.Optional(ATTR_DIR_OF_TRAVEL): cv.slugify,
    vol.Optional(ATTR_INFO): cv.string,
    #-----??Waze Attributes ----------
    vol.Optional(CONF_DISTANCE_METHOD, default='waze'): cv.string,
    vol.Optional(CONF_WAZE_REGION, default='US'): cv.string,
    vol.Optional(CONF_WAZE_MAX_DISTANCE, default=99999): cv.string,
    vol.Optional(CONF_WAZE_MIN_DISTANCE, default=1): cv.string,
    vol.Optional(CONF_WAZE_REALTIME, default=False): cv.boolean,
    vol.Optional(CONF_COMMAND): cv.string
})

def combine_config_filter_parms(p1, p2):
    '''
    Return configuration parms based on the one specified.
    The user may put in the singular version of the parameter or
    a multiple version of the paramter. For example:
        include_device_types: or include_device_type:
    '''
    if p1:
        return p1
    elif p2:
        return p2

    return '_xxx'

#--------------------------------------------------------------------
def setup_scanner(hass, config: dict, see, discovery_info=None):
    """Set up the iCloud Scanner."""
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    account  = config.get(CONF_ACCOUNTNAME,
                         slugify(username.partition('@')[0]))

    if config.get(CONF_MAX_INTERVAL) == '0':
        inzone_interval = config.get(CONF_INZONE_INTERVAL)
    else:
        inzone_interval = config.get(CONF_MAX_INTERVAL)
    max_interval = config.get(CONF_MAX_INTERVAL)
    gps_accuracy_threshold = config.get(CONF_GPS_ACCURACY_THRESHOLD)

    include_device_types = combine_config_filter_parms(config.get(
            CONF_INCLUDE_DEVICETYPES),
            config.get(CONF_INCLUDE_DEVICETYPE))
    include_devices = combine_config_filter_parms(config.get(
            CONF_INCLUDE_DEVICES),
            config.get(CONF_INCLUDE_DEVICE))
    exclude_device_types = combine_config_filter_parms(
            config.get(CONF_EXCLUDE_DEVICETYPES),
            config.get(CONF_EXCLUDE_DEVICETYPE))
    exclude_devices = combine_config_filter_parms(
            config.get(CONF_EXCLUDE_DEVICES),
            config.get(CONF_EXCLUDE_DEVICE))

    unit_of_measurement     = config.get(CONF_UNIT_OF_MEASUREMENT)
    distance_method         = config.get(CONF_DISTANCE_METHOD)
    waze_region             = config.get(CONF_WAZE_REGION)
    waze_max_distance       = config.get(CONF_WAZE_MAX_DISTANCE)
    waze_min_distance       = config.get(CONF_WAZE_MIN_DISTANCE)
    travel_time_factor = config.get(CONF_TRAVEL_TIME_FACTOR)
    waze_realtime           = config.get(CONF_WAZE_REALTIME) 
    
    if waze_region not in WAZE_REGIONS:
        _LOGGER.error("Invalid Waze Region ({}). Valid Values are: "\
                      "NA=US or North America, EU=Europe, IL=Isreal", 
                      waze_region)
        waze_region = 'US'
        waze_max_distance = 0
        waze_min_distance = 0
        
    icloudaccount = Icloud(hass, see, username, password, account, 
        include_device_types, include_devices,
        exclude_device_types, exclude_devices,
        inzone_interval, gps_accuracy_threshold, unit_of_measurement, 
        travel_time_factor, distance_method, 
        waze_region, waze_realtime, waze_max_distance, waze_min_distance)

    if icloudaccount.api:
        ICLOUDTRACKERS[account] = icloudaccount

    else:
        _LOGGER.error("No ICLOUDTRACKERS added")
        return False

#--------------------------------------------------------------------
    def lost_iphone(call):
        """Call the lost iPhone function if the device is found."""
        accounts = call.data.get(CONF_ACCOUNTNAME, ICLOUDTRACKERS)
        devicename = call.data.get(CONF_DEVICENAME)
        for account in accounts:
            if account in ICLOUDTRACKERS:
                ICLOUDTRACKERS[account].lost_iphone(devicename)
    hass.services.register(DOMAIN, 'icloud_lost_iphone', lost_iphone,
                           schema=SERVICE_SCHEMA)

#--------------------------------------------------------------------

    def update_icloud(call):
        """Call the update function of an iCloud account."""
        accounts = call.data.get(CONF_ACCOUNTNAME, ICLOUDTRACKERS)
        devicename = call.data.get(CONF_DEVICENAME)
        command = call.data.get(CONF_COMMAND)
        
        for account in accounts:
            if account in ICLOUDTRACKERS:
                ICLOUDTRACKERS[account].update_icloud(devicename, command)

    hass.services.register(DOMAIN, 'icloud_update', update_icloud,
                           schema=SERVICE_SCHEMA)


#--------------------------------------------------------------------
    def reset_account_icloud(call):
        """Reset an iCloud account."""
        accounts = call.data.get(CONF_ACCOUNTNAME, ICLOUDTRACKERS)
        for account in accounts:
            if account in ICLOUDTRACKERS:
                ICLOUDTRACKERS[account].reset_account_icloud()

    hass.services.register(DOMAIN, 'icloud_reset_account',
                reset_account_icloud, schema=SERVICE_SCHEMA)


#--------------------------------------------------------------------
    def setinterval(call):
        """Call the update function of an iCloud account."""
        accounts = call.data.get(CONF_ACCOUNTNAME, ICLOUDTRACKERS)
        interval = call.data.get(CONF_INTERVAL)
        devicename = call.data.get(CONF_DEVICENAME)

        for account in accounts:
            if account in ICLOUDTRACKERS:
                ICLOUDTRACKERS[account].setinterval(interval, devicename)

    hass.services.register(DOMAIN, 'icloud_set_interval',
                setinterval, schema=SERVICE_SCHEMA)


    # Tells the bootstrapper that the component was successfully initialized
    return True


#====================================================================
class Icloud(DeviceScanner):
    """Representation of an iCloud account."""

    def __init__(self, hass, see, username, password, account, 
        include_device_types, include_devices,
        exclude_device_types, exclude_devices,
        inzone_interval, gps_accuracy_threshold, unit_of_measurement, 
        travel_time_factor, distance_method,
        waze_region, waze_realtime, waze_max_distance, waze_min_distance):
        
        """Initialize an iCloud account."""
        self.hass         = hass
        self.username     = username
        self.password     = password
        self.api          = None
        self.accountname  = account      #name
        self.see          = see

        #string set using the update_icloud command to pass debug commands
        #into icloud3 to monitor operations or to set test variables
        #   gps - set gps acuracy to 234
        #   old - set isold_cnt to 4
        #   interval - toggle display of interval calulation method in info fld
        self.debug_control        = ''
        self.attributes_initialized_flag = False
        
        self.include_device_types = include_device_types.lower()
        self.exclude_device_types = exclude_device_types.lower()
        self.include_devices      = include_devices.lower()
        self.exclude_devices      = exclude_devices.lower()

        self.devices              = {}
        self.seen_this_device_flag = {}
        self.inzone_interval = self._interval_str_to_seconds(
                                     inzone_interval)
        self.gps_accuracy_threshold = int(gps_accuracy_threshold)

        self.unit_of_measurement  = unit_of_measurement
        self.travel_time_factor = float(travel_time_factor)
        
        #Define variables, lists & tables
        if unit_of_measurement == 'mi':
            self.time_format = '%I:%M:%S'
            self.km_mi_factor = 0.62137
        else:
            self.time_format = '%H:%M:%S'
            self.km_mi_factor = 1

        self.last_state               = {}
        self.this_update_seconds      = 0
        self.overrideinterval_seconds = {}
        self.interval_seconds         = {}
        self.interval_str             = {}
        self.went_3km                 = {} #if more than 2 km/mi, probably driving
        self.last_update_time         = {}
        self.last_update_seconds      = {}
        self.next_update_seconds      = {}
        self.next_update_time         = {}
        self.poll_count               = {}
        self.poll_count_yesterday     = {}
        self.update_in_process_flag   = {}
        self.location_isold_cnt       = {}    # override interval while < 4
        self.tracked_devices          = ''
        self.update_inprocess_flag    = False
        self.immediate_retry_flag     = False
        self.time_zone_offset_seconds   = 0
        self.setinterval_cmd_devicename = None
        
        #get home zone location
        self.zone_home        = self.hass.states.get('zone.home').attributes
        self.zone_home_lat    = self.zone_home['latitude']
        self.zone_home_long   = self.zone_home['longitude']
        self.zone_home_radius = round(self.zone_home['radius']/1000, 4)
        self.zone_home_radius_near = round(self.zone_home_radius * 5, 2)
        
        #used to calculate distance traveled since last poll
        self.last_lat       = {}
        self.last_long      = {}
        self.stationary_cnt = {}
        self.waze_time      = {}
        self.waze_dist      = {}
        self.calc_dist      = {}
        self.dist           = {}
        
        self.zone_change_flag       = {}
        self.poor_gps_accuracy_flag = {}
        self.poor_gps_accuracy_cnt  = {}
       
        #Setup Waze parameters
        self.distance_method_waze_flag = (distance_method.lower() == 'waze')

        #ok=0, not used=1, paused=2, out-of-range=3, error=4
        if self.distance_method_waze_flag:
            self.waze_status = WAZE_USED
        else:
            self.waze_status = WAZE_NOT_USED
        
        self.waze_region = waze_region
        self.waze_adjustment = 0
        #       See if distance adjustment factors were used
        if '+' in waze_max_distance:
            waze_max_distance    = waze_max_distance.split('+')[0]
            self.waze_adjustment = waze_max_distance.split('+')[1]
        elif '-' in waze_max_distance:
            waze_max_distance    = waze_max_distance.split('-')[0]
            self.waze_adjustment = waze_max_distance.split('-')[1] * -1

        self.waze_min_distance   = round(float(waze_min_distance) / \
                                            self.km_mi_factor, 2)
        self.waze_max_distance   = round(float(waze_max_distance) / \
                                            self.km_mi_factor, 2)
        self.waze_max_dist_save  = self.waze_max_distance
        self.waze_realtime       = waze_realtime

        self._trusted_device     = None
        self._verification_code  = None

        self._attrs = {}
        self._attrs[CONF_ACCOUNTNAME] = account     #name

        self.reset_account_icloud()

        #add HA event that will call the _device_polling_15_sec_timer_loop function every 15 seconds
        #that will check a iphone's location if the time interval
        #has passed. If so, update all tracker attributes for all phones
        #being tracked with the new information.

        track_utc_time_change(self.hass, self._device_polling_15_sec_timer_loop,
                              second=[0, 15, 30, 45])

#--------------------------------------------------------------------
    def reset_account_icloud(self):
        """Reset an iCloud account."""
        from pyicloud import PyiCloudService
        from pyicloud.exceptions import (
            PyiCloudFailedLoginException, PyiCloudNoDevicesException)

        _LOGGER.info(("??????? ICLOUD3.PY ACCOUNT/INITIALIZATION " 
                     "??????? %s ???????"), self.username)

        self.time_zone_offset_seconds = self._calculate_time_zone_offset()

        icloud_dir = self.hass.config.path('icloud')
        if not os.path.exists(icloud_dir):
            os.makedirs(icloud_dir)

        try:
            self.api = PyiCloudService(self.username, self.password,
                       cookie_directory=icloud_dir, verify=True)
        except PyiCloudFailedLoginException as error:
            self.api = None
            _LOGGER.error("Error logging into iCloud Service: %s", error)
            return

        try:
            self.devices     = {}
            self.device_type = {}
            self.overrideinterval_seconds = {}
            self.tracking_device_flag      = {}

            _LOGGER.info(("??WAZE SETTINGS: Region=%s, Realtime=%s, "
                          "MaxDistance=%s, MinDistance=%s"),
                          self.waze_region, self.waze_realtime, 
                          self.waze_max_distance, self.waze_min_distance)
            _LOGGER.info(("??FILTERS: include_device_types=%s,"
                         " include_devices=%s, exclude_device_types=%s,"
                         " exclude_devices=%s, filter=%s"),
                         self.include_device_types, self.include_devices,
                         self.exclude_device_types, self.exclude_devices)

            _LOGGER.info("??INITIALIZING DEVICE TRACKING ?? USER ~~%s~~",
                            self.username)

            for device in self.api.devices:
                status      = device.status(DEVICESTATUSSET)
                location    = status['location']
                devicename  = slugify(status['name'].replace(' ', '', 99))
                device_type = status['deviceClass'].lower()

                if location is None:
                    _LOGGER.info(("??Not tracking %s, No location "
                                 "information"),
                                 devicename)
                    tracking_flag = False
                elif status['locationEnabled'] is False:
                    _LOGGER.info(("??Not tracking %s, Location Disabled"),
                                 devicename)
                    tracking_flag = False
                elif status['deviceStatus'] == '204':
                    _LOGGER.info(("??Not tracking %s, Unregistered "
                                 "Device (Status=204)"), devicename)
                    tracking_flag = False
                elif devicename in self.tracking_device_flag:
                    _LOGGER.info(("??Not tracking %s, Multiple "
                                 "devices with same name"),
                                 devicename)
                    tracking_flag = False
                else:
                    tracking_flag = self._check_tracking_this_device(
                                    devicename, device_type)

                self.tracking_device_flag[devicename] = tracking_flag
                if tracking_flag is False:
                    continue

                self.tracked_devices = '{} {},'.format(self.tracked_devices,
                            devicename)
                self.devices[devicename]     = device
                self.device_type[devicename] = device_type

                self.last_update_time[devicename]    = '00:00:00'
                self.last_update_seconds[devicename] = 0
                self.next_update_time[devicename]    = '00:00:00'
                self.next_update_seconds[devicename] = 0
                self.went_3km[devicename]            = False
                self.poll_count[devicename]           = 0
                self.poll_count_yesterday[devicename] = 0
                self.overrideinterval_seconds[devicename] = 0
                self.interval_seconds[devicename]    = 0
                self.interval_str[devicename]        = '0 sec'
                self.last_state[devicename]        = \
                                        self._get_current_state(devicename)
                self.stationary_cnt[devicename]       = 0
                self.location_isold_cnt[devicename]   = 0
                self.last_lat[devicename]             = self.zone_home_lat
                self.last_long[devicename]            = self.zone_home_long
                self.poor_gps_accuracy_flag[devicename] = False
                self.poor_gps_accuracy_cnt[devicename]  = 0
                self.update_in_process_flag[devicename] = False
                self.seen_this_device_flag[devicename]  = False
                self.zone_change_flag[devicename]       = False
                
                #Initialize the new attributes
                kwargs                         = {}
                attrs                          = {}
                attrs[ATTR_LAST_UPDATE_TIME]   = '00:00:00'
                attrs[ATTR_NEXT_UPDATE_TIME]   = '00:00:00'
                attrs[ATTR_LAST_LOCATED]       = '00:00:00'
                attrs[ATTR_DISTANCE]           = 0
                attrs[ATTR_WAZE_TIME]          = ''
                attrs[ATTR_CALC_DISTANCE]      = 0
                attrs[ATTR_WAZE_DISTANCE]      = 0
                attrs[ATTR_POLL_COUNT]         = 0
                attrs[ATTR_DIR_OF_TRAVEL]      = ''
                attrs[ATTR_INFO]               = ''
                attrs[ATTR_TRACKED_DEVICES]    = self.tracked_devices
                attrs[CONF_TRAVEL_TIME_FACTOR] = self.travel_time_factor
                attrs[CONF_WAZE_MIN_DISTANCE]  = \
                        self._km_to_mi(self.waze_min_distance)
                attrs[CONF_WAZE_MAX_DISTANCE]  = \
                        self._km_to_mi(self.waze_max_distance)

                self._update_device_attributes(devicename, kwargs, attrs)

        except PyiCloudNoDevicesException:
            _LOGGER.error('No iCloud Devices found!')

#--------------------------------------------------------------------
    def icloud_trusted_device_callback(self, callback_data):
        """Handle chosen trusted devices."""
        self._trusted_device = int(callback_data.get('trusted_device'))
        self._trusted_device = self.api.trusted_devices[self._trusted_device]

        if not self.api.send_verification_code(self._trusted_device):
            _LOGGER.error("Failed to send verification code")
            self._trusted_device = None
            return

        if self.accountname in _CONFIGURING:
            request_id   = _CONFIGURING.pop(self.accountname)
            configurator = self.hass.components.configurator
            configurator.request_done(request_id)

        # Trigger the next step immediately
        self.icloud_need_verification_code()

#--------------------------------------------------------------------
    def icloud_need_trusted_device(self):
        """We need a trusted device."""
        configurator = self.hass.components.configurator
        if self.accountname in _CONFIGURING:
            return

        devicesstring = ''
        devices = self.api.trusted_devices
        for i, device in enumerate(devices):
            devicename = device.get(
                'deviceName', 'SMS to %s' % device.get('phoneNumber'))
            devicesstring += "{}: {};".format(i, devicename)

        _CONFIGURING[self.accountname] = configurator.request_config(
            'iCloud {}'.format(self.accountname),
            self.icloud_trusted_device_callback,
            description=('Please choose your trusted device by entering'
                    ' the index from this list: ' + devicesstring),
            entity_picture="/static/images/config_icloud.png",
            submit_caption='Confirm',
            fields=[{'id': 'trusted_device', 'name': 'Trusted Device'}]
        )

#--------------------------------------------------------------------
    def icloud_verification_callback(self, callback_data):
        """Handle the chosen trusted device."""
        from pyicloud.exceptions import PyiCloudException
        self._verification_code = callback_data.get('code')

        try:
            if not self.api.validate_verification_code(
                    self._trusted_device, self._verification_code):
                raise PyiCloudException('Unknown failure')
        except PyiCloudException as error:
            # Reset to the initial 2FA state to allow the user to retry
            _LOGGER.error("Failed to verify verification code: %s", error)
            self._trusted_device = None
            self._verification_code = None

            # Trigger the next step immediately
            self.icloud_need_trusted_device()

        if self.accountname in _CONFIGURING:
            request_id   = _CONFIGURING.pop(self.accountname)
            configurator = self.hass.components.configurator
            configurator.request_done(request_id)

#--------------------------------------------------------------------
    def icloud_need_verification_code(self):
        """Return the verification code."""
        configurator = self.hass.components.configurator
        if self.accountname in _CONFIGURING:
            return

        _CONFIGURING[self.accountname] = configurator.request_config(
            'iCloud {}'.format(self.accountname),
            self.icloud_verification_callback,
            description    = ('Please enter the validation code:'),
            entity_picture = "/static/images/config_icloud.png",
            submit_caption='Confirm',
            fields=[{'id': 'code', 'name': 'code'}]
        )

#########################################################
#
#   This function is called every 15 seconds by HA. Cycle through all
#   of the iCloud devices to see if any of the ones being tracked need
#   to be updated. If so, we might as well update the information for
#   all of the devices being tracked since PyiCloud gets data for
#   every device in the account.
#
#########################################################

    def _device_polling_15_sec_timer_loop(self, now):
        """Keep the API alive. Will be called by HA every 15 seconds"""

        self.this_update_seconds = \
                self._time_to_seconds(dt_util.now().strftime('%X'))
        this_update_time = dt_util.now().strftime(self.time_format)

        if self.api is None:
            _LOGGER.info("??iCloud account needs to be reset")
            self.reset_account_icloud()

        if self.api is None:
            _LOGGER.info("??iCloud account reset failed - no devices")
            return

        if self.api.requires_2fa:
            from pyicloud.exceptions import PyiCloudException
            try:
                if self._trusted_device is None:
                    self.icloud_need_trusted_device()
                    return

                if self._verification_code is None:
                    self.icloud_need_verification_code()
                    return

                self.api.authenticate()
                if self.api.requires_2fa:
                    raise Exception('Unknown failure')

                self._trusted_device    = None
                self._verification_code = None
            except PyiCloudException as error:
                _LOGGER.error("??Error setting up 2FA: %s", error)

        try:
            #Set update in process flag used in the 'icloud_update' external
            #command service call. Otherwise, the service call might be
            #overwritten if we are doing an update when it was started.
            self.update_inprocess_flag = True
            
            for devicename in self.devices:
                if (self.tracking_device_flag.get(devicename) is False or
                   self.next_update_time.get(devicename) == 'Paused'):
                    continue

                current_state = self._get_current_state(devicename)

                # If the state changed since last poll, force an update
                # This can be done via device_tracker.see service call
                # with a different location_name in an automation or
                # from entering a zone via the IOS App.
                if current_state != self.last_state.get(devicename):
                    _LOGGER.debug(("??Device State changed, ~~%s~~, "
                         " From=%s, To=%s"), devicename,
                         self.last_state.get(devicename), current_state)
                        
                    self.zone_change_flag[devicename]    = True
                    self.last_state[devicename]          = current_state
                    self.stationary_cnt[devicename]      = 0
                    self.next_update_seconds[devicename] = 0

                    attrs  = {}
                    kwargs = {}                 
                    self._update_device_attributes(devicename, kwargs, attrs)
                    
                #This flag will be 'true' if the last update for this device
                #was not completed. Do another update now.
                if self.update_in_process_flag.get(devicename):
                    _LOGGER.debug(("??RETRYING UPDATE - Device update was not "
                                    "completed in last cycle ~~%s~~ "),
                                    devicename)

                    self._update_all_devices(devicename)
                    
                elif (self.this_update_seconds >= 
                            self.next_update_seconds.get(devicename)):

                    self._update_all_devices(devicename)
                    
            self.update_inprocess_flag = False
            
        except ValueError:
            _LOGGER.debug("iCloud API returned an error")
            
            self.api.authenticate()                 #Reset iCloud
            self._update_all_devices(devicename)    #Now, update devices
            self.update_inprocess_flag = False

#########################################################
#
#   Cycle through all iCloud devices and update the information for the devices
#   being tracked
#
#########################################################

    def _update_all_devices(self, arg_devicename):
        """
        Request device information from iCloud (if needed) and update
        device_tracker information.
        """

        from pyicloud.exceptions import PyiCloudNoDevicesException

#        self.devices[arg_devicename].location()

        if self.api is None:
            _LOGGER.info(("Update Device Error, %s, "
                         "No api information for device. Reauthenticating"),
                         arg_devicename)
            return

        try:
            for device in self.api.devices:
                status = device.status(DEVICESTATUSSET)
                if status is None:
                    _LOGGER.info(("Update Device Error, %s, "
                         "No data returned for device. Reauthenticating"),
                         arg_devicename)
                    return

                location   = status['location']
                devicename = slugify(status['name'].replace(' ', '', 99))
                battery    = int(status.get('batteryLevel', 0) * 100)

                if ((self.tracking_device_flag.get(devicename) is False) or 
                            (self.next_update_time.get(devicename) ==
                            'Paused')):
                    continue

                _LOGGER.debug("??????? UPDATE DEVICE <START> ??????? "\
                                "%s ???????", devicename)

                if self.update_in_process_flag[devicename]:
                    update_msg = "Last update not completed, retrying"
                else:
                    update_msg = "Updating" 
                update_msg = "? {} {} ?".format(update_msg, status['name'])

                attrs = {}
                kwargs = {}
                attrs[ATTR_INFO] = update_msg                  
                self._update_device_attributes(devicename, kwargs, attrs)

                #set device being updated flag. This is checked in the 
                #'_device_polling_15_sec_timer_loop' loop to make sure the last update
                #completed successfully (Waze has a compile error bug that will
                #kill update and everything will sit there until the next poll.
                #if this is still set in '_device_polling_15_sec_timer_loop', repoll
                #immediately!!!
                self.update_in_process_flag[devicename] = True
               
#                _LOGGER.debug("??Device Status=%s", status)

                c = float(self.poll_count.get(devicename)) + 1
                self.poll_count[devicename] = c
                            
                if not location:
                    attrs    = {}
                    attrs[CONF_INTERVAL] = 'Error: No Location Data'
                    time_stamp = 'No Location Data'
                    self.last_state[devicename] = 'unknown'
                    
                else:
                    # If old, this function will sleep for 2 seconds, then
                    # do another poll, up to 4 times before returning with
                    # the last location data.
                    if location['isOld'] or 'old' in self.debug_control:
                        location = self._retry_setup_location_data(
                                    device, devicename, location)

                    time_stamp = self._format_timestamp(location['timeStamp'])
                    latitude   = location[ATTR_LATITUDE]
                    longitude  = location[ATTR_LONGITUDE]
                    
                    location_isold_flag, isold_cnt = \
                            self._check_isold_status(devicename, 
                                        location['isOld'], time_stamp)

                    _LOGGER.debug(("??Location Info Checked, ~~%s~~, "
                          "TimeStamp=%s(%s), Long=%s, "
                          "Lat=%s, isOldFlag=%s, isOldRetryCnt=%s"),
                          devicename, location['timeStamp'], time_stamp,
                          longitude, latitude,
                          location_isold_flag, isold_cnt)

                    gps_accuracy = int(location['horizontalAccuracy'])
                    if 'gps' in self.debug_control:  gps_accuracy = 234 #debug
                    self.poor_gps_accuracy_flag[devicename] = \
                            (gps_accuracy > self.gps_accuracy_threshold)
                     
                    if not self.poor_gps_accuracy_flag.get(devicename):
                        self.poor_gps_accuracy_cnt[devicename] = 0

                    #Calculate polling interval and setup location attributes
                    attrs = self._determine_interval(devicename,
                                  latitude, longitude, battery,
                                  gps_accuracy, location_isold_flag)
 
                    # Double check state, it can be wrong during ha startup
                    if self.last_state.get(devicename) == 'Unknown':
                        current_zone = self._get_current_zone(latitude, longitude)
                        self.last_state[devicename] = current_zone
                        
       #             if current_zone != self.last_state.get(devicename):
       #             dist_from_home = float(attrs[ATTR_DISTANCE])
       #             if float(dist_from_home) < .05:
       #                 current_zone = 'home'
       #                 self.went_3km[devicename] = False
                # End of 'if not location:' statement
                
                _LOGGER.debug("??Location Attributes, State=%s, Attrs=%s", 
                                self.last_state.get(devicename), attrs)
                                   
                attrs[CONF_ACCOUNTNAME]        = self.accountname
                attrs[ATTR_LAST_LOCATED]       = time_stamp
                attrs[ATTR_DEVICESTATUS]       = DEVICESTATUSCODES.get(
                                status['deviceStatus'], 'error')
                attrs[ATTR_LOWPOWERMODE]       = status['lowPowerMode']
                attrs[ATTR_BATTERYSTATUS]      = status['batteryStatus']
                attrs[ATTR_TRACKED_DEVICES]    = self.tracked_devices[:-1]
                
                if self.poor_gps_accuracy_cnt.get(devicename) > 0:
                    attrs[ATTR_POLL_COUNT]  = "{}-GPS".format(\
                            self.poor_gps_accuracy_cnt.get(devicename))
                elif self.stationary_cnt.get(devicename) > 0:
                    attrs[ATTR_POLL_COUNT]  = "{}-Statnry".format(\
                            self.stationary_cnt.get(devicename))
                elif self.location_isold_cnt.get(devicename) > 0:
                    attrs[ATTR_POLL_COUNT]  = "{}-OldLoc".format(\
                            self.location_isold_cnt.get(devicename))
                else:
                    attrs[ATTR_POLL_COUNT]  = \
                            int(self.poll_count.get(devicename))

                kwargs              = {}
                kwargs['host_name'] = status['name']
                kwargs['battery']   = int(battery)

                self._update_device_attributes(devicename, kwargs, attrs)
               
                self.seen_this_device_flag[devicename]  = True
                self.update_in_process_flag[devicename] = False
                
                _LOGGER.info(("??Device %s tracker information has been "
                         "updated, State=%s, Interval=%s, TravelTime=%s, "
                         "Distance=%s, NextUpdate=%s,  Direction=%s, "
                         "PollCnt=%s, GPSAccuracy=%s"), 
                         devicename, self.last_state.get(devicename),
                         attrs[CONF_INTERVAL],
                         attrs[ATTR_WAZE_TIME], attrs[ATTR_DISTANCE], 
                         attrs[ATTR_NEXT_UPDATE_TIME], 
                         attrs[ATTR_DIR_OF_TRAVEL],
                         attrs[ATTR_POLL_COUNT], attrs[ATTR_GPS_ACCURACY])
                _LOGGER.debug(("??????? UPDATING DEVICE <END> ??????? "
                        "%s ???????"), devicename)

        except PyiCloudNoDevicesException:
            _LOGGER.error("No iCloud Devices found")
            
#########################################################
#
#   Calculate polling interval based on zone, distance from home and
#   battery level. Setup triggers for next poll
#
#########################################################

    def _determine_interval(self, devicename, latitude, longitude,
                                battery, gps_accuracy,
                                location_isold_flag):
        """Calculate new interval. Return location based attributes"""
        
        
        location_data = self._get_device_distance_data(devicename,
                                    latitude, longitude, gps_accuracy)

        current_zone              = location_data[0]
        direction_of_travel       = location_data[1]
        dist_from_home            = location_data[2]
        dist_from_home_moved      = location_data[3]
        dist_last_poll_move       = location_data[4]
        waze_dist_from_home       = location_data[5]
        calc_dist_from_home       = location_data[6]
        waze_dist_from_home_moved = location_data[7]
        calc_dist_from_home_moved = location_data[8]
        waze_dist_last_poll_moved = location_data[9]
        calc_dist_last_poll_moved = location_data[10]
        waze_time_from_home       = location_data[11]

        _LOGGER.debug(("??DETERMINE INTERVAL <START>, ~~%s~~, "
                      "location_data=%s"), devicename, location_data)
                      
#       the following checks the distance from home and assigns a
#       polling interval in minutes.  It assumes a varying speed and
#       is generally set so it will poll one or twice for each distance
#       group. When it gets real close to home, it switches to once
#       each 15 seconds so the distance from home will be calculated
#       more often and can then be used for triggering automations
#       when you are real close to home. When home is reached,
#       the distance will be 0.

        stationary_cnt = 0
        interval = 15
        interval_multiplier = 1
        
        log_method = ''
        log_msg   = ''
        log_value = ''
        if self.zone_change_flag.get(devicename):
            interval = 15       #changed or left zone, override everything
            log_method="1-ZoneChanged"
            log_msg   = 'Zone={}/{}'.format(self.last_state.get(devicename),
                                current_zone)

        elif (self.poor_gps_accuracy_flag.get(devicename)):
            interval   = 60      #poor accuracy, try again in 1 minutes
            log_method = '2-PoorGPS'
            
        elif self.overrideinterval_seconds.get(devicename) > 0:
            interval   = self.overrideinterval_seconds.get(devicename)
            log_method = '3-Override'

        elif location_isold_flag:
            if (self.location_isold_cnt.get(devicename) % 2 == 0):
                interval = 15       #15 sec, try again soon
            elif (self.location_isold_cnt.get(devicename) % 10 == 0):
                interval = 600      #10 min, lots of many retrys, take a break
            log_method   = '4-OldLoctionData'
            log_msg      = 'Cnt={}'.format(\
                                self.location_isold_cnt.get(devicename))
            
        elif current_zone != 'not_home' or dist_from_home == 0:
            interval   = self.inzone_interval
            log_method = '5-InZone'
            log_msg    = 'Zone={}'.format(current_zone)
            
        elif dist_from_home < 2.5 and self.went_3km.get(devicename):  #1.5 mi
            interval   = 15       #real close and driving, poll every 15 sec
            log_method = '6- Dist < 2.5km(1.5mi)'

        elif dist_from_home < 3.5:      #2 mi
            interval   = 30               #30 sec
            log_method = '7-Dist < 3.5km(2mi)'
            
        elif self.waze_status == WAZE_USED and waze_time_from_home > 300:
            interval   = round(waze_time_from_home * \
                         self.travel_time_factor, 0) #travel time*factor(.75)
            log_method = '8-WazeTime'
            log_msg    = 'TimeFmHome={}'.format(waze_time_from_home)
            
        elif dist_from_home < 5:        #3 mi
            interval   = 60               #1 min
            log_method = '9-Dist < 5km(3mi)'
            
        elif dist_from_home < 8:        #5 mi
            interval   = 120              #2 min
            log_method = '10-Dist < 8km(5mi)'
            
        elif dist_from_home < 12:       #7.5 mi
            interval   = 180              #3 min
            log_method = '11-Dist < 12km(7mi)'

        elif dist_from_home < 20:       #12 mi
            interval   = 600              #10 min
            log_method = '12-Dist < 20km(12mi)'

        elif dist_from_home < 40:       #25 mi
            interval   = 900              #15 min
            log_method = '13-Dist < 40km(25mi)'

        elif dist_from_home > 150:      #90 mi
            interval   = 3600             #1 hr
            log_method = '14-Dist > 150km(90mi)'

        else:
            interval = \
                round(self._km_to_mi(dist_from_home) / 1.5, 0) * 60
            log_method = '15-Calculated'
            log_msg    = 'Value={}/1.5'.format(self._km_to_mi(dist_from_home))

        #set stationary & away_from interval multiplier
        if 'stationary' in direction_of_travel:
            stationary_cnt = self.stationary_cnt.get(devicename) + 1
            direction_of_travel = 'Stationary'
            if stationary_cnt % 3 == 0:
                interval_multiplier = 3    #calc-increase timer every 3rd poll
                log_method_im = '21-Stationry mod 3'.format(log_method)
            elif stationary_cnt % 2 == 0:
                interval_multiplier = 2    #calc-increase timer every 2nd poll
                log_method_im = '22-Stationry mod 2'
        elif 'away_from' in direction_of_travel and distance_method == 'calc':
            interval_multiplier = 2    #calc-increase timer
            log_method_im = '24-Away+Calc'

        self.stationary_cnt[devicename] = stationary_cnt

        #if changed zones on this poll, clear flags and reset multiplier
        if self.zone_change_flag.get(devicename):         
            self.zone_change_flag[devicename] = False
            interval_multiplier = 1
            
        #Check accuracy again to make sure nothing changed, update counter
        if self.poor_gps_accuracy_flag.get(devicename):
            interval_multiplier = 1
            gps_cnt = self.poor_gps_accuracy_cnt.get(devicename) + 1
            self.poor_gps_accuracy_cnt[devicename] = gps_cnt
            
        #Real close, final check to make sure interval is not adjusted
        if interval <= 60 or \
                (battery > 0 and battery <= 33 and interval >= 120):
            interval_multiplier = 1
            
        interval     = interval * interval_multiplier
        interval_str = self._seconds_to_time_str(interval)

        interval_debug_msg = "?{}, Interval={}, Distance={}, {}".format( \
                    log_method, interval_str, 
                    self._km_to_mi(dist_from_home), log_msg)
 
        if interval_multiplier != 1:
           interval_str = '{}(x{})'.format(interval_str, interval_multiplier)
           interval_debug_msg = "{}, Multiplier={}({})".format(\
                    interval_debug_msg, interval_multiplier, log_method_im)

        #check if next update is past midnight (next day), if so, adjust it
        next_poll = self.this_update_seconds + interval
        if next_poll >= 86400:
            next_poll -= 86400
            self.poll_count_yesterday[devicename] = self.poll_count[devicename]
            self.poll_count[devicename] = 1
 
        # Update all dates and other fields
        self.interval_seconds[devicename]    = interval
        self.next_update_seconds[devicename] = next_poll
        self.next_update_time[devicename]    = \
                    self._seconds_to_time(next_poll)
        self.last_update_time[devicename]    = \
                    self._seconds_to_time(self.this_update_seconds)
        self.last_update_seconds[devicename] = self.this_update_seconds
        self.interval_str[devicename]        = interval_str

        #if more than 3km(1.8mi) then assume driving, used later above
        if dist_from_home > 3:                # 1.8 mi
            self.went_3km[devicename] = True
        elif dist_from_home < .03:            # home, reset flag
             self.went_3km[devicename] = False

        info = self._setup_info_attr(devicename, battery, gps_accuracy,
                                stationary_cnt, dist_last_poll_move,
                                current_zone, location_isold_flag)

        _LOGGER.debug("??INTERVAL FORMULA, {}".format(interval_debug_msg))

        if 'interval' not in self.debug_control:
            interval_debug_msg = ''
            
        _LOGGER.debug(("??DETERMINE INTERVAL <COMPLETE>,  ~~%s~~, "
                      "This poll: %s(%s), Last Update: %s(%s), "
                      "Next Update: %s(%s),  Interval: %s*%s, "
                      "OverrideInterval=%s, DistTraveled=%s"),
                      devicename,
                      self._seconds_to_time(self.this_update_seconds),
                      self.this_update_seconds,
                      self.last_update_time.get(devicename),
                      self.last_update_seconds.get(devicename),
                      self.next_update_time.get(devicename),
                      self.next_update_seconds.get(devicename),
                      self.interval_str.get(devicename),
                      interval_multiplier,
                      self.overrideinterval_seconds.get(devicename),
                      dist_last_poll_move)
                      
        self.last_state[devicename] = current_zone
        attrs = {}

        #if poor gps and moved less than 1km, redisplay last distances
        if self.poor_gps_accuracy_flag.get(devicename) and \
                        dist_last_poll_move < 1:
            dist_from_home      = self.dist.get(devicename)
            waze_dist_from_home = self.waze_dist.get(devicename)
            calc_dist_from_home = self.calc_dist.get(devicename)
            waze_time_msg       = self.waze_time.get(devicename)
        else:        
            waze_time_msg       = self._format_waze_time_msg(devicename, 
                                            waze_time_from_home, 
                                            waze_dist_from_home)
            dist_from_home      = self._km_to_mi(dist_from_home)
            waze_dist_from_home = self._km_to_mi(waze_dist_from_home)
            calc_dist_from_home = self._km_to_mi(calc_dist_from_home)

            #save for next poll if poor gps
            self.dist     [devicename] = dist_from_home
            self.waze_dist[devicename] = waze_dist_from_home
            self.waze_time[devicename] = waze_time_msg
            self.calc_dist[devicename] = calc_dist_from_home

        attrs[CONF_INTERVAL]           = interval_str
        attrs[ATTR_LAST_UPDATE_TIME]   = \
                    self._seconds_to_time(self.this_update_seconds)
        attrs[ATTR_NEXT_UPDATE_TIME]   = \
                    self._seconds_to_time(next_poll)

        attrs[ATTR_WAZE_TIME]         = waze_time_msg
        attrs[ATTR_DISTANCE]          = dist_from_home
        attrs[ATTR_CALC_DISTANCE]     = calc_dist_from_home
        attrs[ATTR_WAZE_DISTANCE]     = waze_dist_from_home
        attrs[ATTR_DIR_OF_TRAVEL]     = direction_of_travel
        
        attrs[ATTR_LATITUDE]          = latitude
        attrs[ATTR_LONGITUDE]         = longitude
        attrs[ATTR_GPS_ACCURACY]      = gps_accuracy

        attrs[ATTR_INFO]              = interval_debug_msg + info
           
        _LOGGER.debug(("??DETERMINE INTERVAL <EXIT>, ~~%s~~, "
                      "location_attributes=%s"), devicename, attrs)
 
        return attrs
  
#########################################################
#
#   UPDATE DEVICE ATTRIBUTESNS
#
#########################################################
    def _get_current_state(self, devicename):
        """
        Get current state of the device_tracker entity
        (home, away, other state)
        """

        entity_id = self._format_entity_id(devicename)
        try:
            device_state = self.hass.states.get(entity_id).state

            if device_state:
                return device_state

            return 'not_home'

        except:
            return 'Unknown'

#--------------------------------------------------------------------
    def _update_device_attributes(self, devicename, kwargs: str=None, 
                        attrs: str=None):
        """
        Update the device and attributes with new information
        On Entry, kwargs = {} or contains the base attributes
        """

        if not kwargs: kwargs = {}
        if not attrs:  attrs  = {}
        
        kwargs['dev_id']         = devicename
        kwargs['location_name']  = self.last_state.get(devicename)
        kwargs[ATTR_ATTRIBUTES]  = attrs

        self.see(**kwargs)

        return
#--------------------------------------------------------------------    
    def _get_device_attributes(self, devicename):
        """
        Get attributes of the device
        """
        try:
            entity_id = self._format_entity_id(devicename)
        
            return self.hass.states.get(entity_id).attributes
        except:
            return "<<<No attributes>>>"
#--------------------------------------------------------------------    
    def _get_current_zone(self, latitude, longitude):
        """
        Get current zone of the device based on the location
        """

        current_zone = active_zone(self.hass, latitude, longitude)

        if current_zone:
            current_zone = current_zone.attributes.get('friendly_name')
        else:
            current_zone = 'not_home'

        return current_zone.lower()
#--------------------------------------------------------------------
    def _format_entity_id(self, devicename):
 
        return '{}.{}'.format(DOMAIN, devicename)
#--------------------------------------------------------------------
    def _TRACE_ATTRS(self, devicename, lineno):
        all_attrs  = self._get_device_attributes(devicename)
        _LOGGER.debug("??Attrs??%s=%s", lineno, all_attrs)
        
        if len(all_attrs) ==  0:
            _LOGGER.debug("?????? Attrs Empty ??????")
        return
#########################################################
#
#   UPDATE DEVICE LOCATION & INFORMATION ATTRIBUTE FUNCTIONS
#
#########################################################

    def _get_device_distance_data(self, devicename, latitude, longitude,
                                gps_accuracy):
        """ Determine the location of the device.
            Returns:
                - current_zone (current zone from lat & long)
                  set to 'home' if distance < home zone radius
                - dist_from_home (mi or km)
                - dist_traveled (since last poll)
                - direction_of_travel (towards, away_from, stationary, in_zone)
        """
        
        _LOGGER.debug("??SETUP_LOC_ATTRS <START> ~~%s~~", devicename) 
        
        if self.seen_this_device_flag.get(devicename):
            attrs = self._get_device_attributes(devicename)
 
            _LOGGER.debug("??ATTRIBUTES ~~%s~~ %s", devicename,
                            attrs) 
            
            last_waze_time         = attrs[ATTR_WAZE_TIME]
            last_dir_of_travel     = attrs[ATTR_DIR_OF_TRAVEL]
            last_dist_from_home_s  = attrs[ATTR_DISTANCE]
            last_dist_from_home    = round(float(last_dist_from_home_s), 2)
                                              #make km again for calculations
            last_dist_from_home    = last_dist_from_home / self.km_mi_factor
                             
            last_lat  = self.last_lat.get(devicename)
            last_long = self.last_long.get(devicename)
           
        else:
            last_dir_of_travel  = 'unknown'
            last_dist_from_home = 0
            last_lat  = self.zone_home_lat
            last_long = self.zone_home_long
  
        #get last interval 
        interval_str = self.interval_str.get(devicename)
        interval = self._interval_str_to_seconds(interval_str)
        
        this_lat  = latitude
        this_long = longitude
        
        current_zone = self._get_current_zone(this_lat, this_long)
        
        _LOGGER.debug(("??Lat-long-GPS Initialized >>>, "
              "this_lat=%s, this_long=%s, "
              "last_lat=%s, last_long=%s, "
              "latitude=%s, longitude=%s, "
              "GPS.Accur=%s, GPS.Threshold=%s"),
              this_lat, this_long, last_lat, last_long, latitude, longitude,
              gps_accuracy, self.gps_accuracy_threshold)

        # Get Waze distance & time
        #   Will return [error, 0, 0, 0] if error
        #               [out_of_range, dist, time, info] if
        #                           last_dist_from_home > 
        #                           last distance from home
        #               [ok, 0, 0, 0]  if zone=home
        #               [ok, distFmHome, timeFmHome, info] if OK
        
        calc_dist_from_home       = self._calc_distance(this_lat, this_long,
                                    self.zone_home_lat, self.zone_home_long)
        calc_dist_last_poll_moved = self._calc_distance(last_lat, last_long,
                                    this_lat, this_long)
        calc_dist_from_home_moved = round(calc_dist_from_home 
                                     - last_dist_from_home, 2)

        #Use Calc if close to home, Waze not accurate when close
        if calc_dist_from_home <= 1:
            self.waze_status          = WAZE_PAUSED
            waze_dist_from_home       = calc_dist_from_home
            waze_time_from_home       = 0
            waze_dist_last_poll_moved = calc_dist_last_poll_moved
            waze_dist_from_home_moved = calc_dist_from_home_moved
        elif self.distance_method_waze_flag:
            self.waze_status          = WAZE_USED
            waze_dist_time_info = self._get_waze_data(this_lat, this_long,
                                            last_lat, last_long, current_zone,
                                            last_dist_from_home)
            self.waze_status          = waze_dist_time_info[0]
            waze_dist_from_home       = waze_dist_time_info[1]
            waze_time_from_home       = waze_dist_time_info[2]
            waze_dist_last_poll_moved = waze_dist_time_info[3]
            waze_dist_from_home_moved = round(waze_dist_from_home
                                        - last_dist_from_home, 2)

        #don't reset data if poor gps, use the best we have
        if current_zone == 'home'and \
                    not self.poor_gps_accuracy_flag.get(devicename):
            distance_method      = 'Home'
            dist_from_home       = 0
            dist_last_poll_moved = 0
            dist_from_home_moved = 0
        elif self.waze_status == WAZE_USED:
            distance_method      = 'Waze'
            dist_from_home       = waze_dist_from_home
            dist_last_poll_moved = waze_dist_last_poll_moved
            dist_from_home_moved = waze_dist_from_home_moved
        else:
            distance_method      = 'Calc'
            dist_from_home       = calc_dist_from_home
            dist_last_poll_moved = calc_dist_last_poll_moved
            dist_from_home_moved = calc_dist_from_home_moved
 
        self.last_lat[devicename]  = this_lat
        self.last_long[devicename] = this_long
        
        _LOGGER.debug(("??Distances calculated >>>, "
              "Zone=%s, Method=%s, ZoneRadius=%s, LastDistFmHome=%s "
              "WazeStatus=%s"),
              current_zone, distance_method, self.zone_home_radius,
              last_dist_from_home, self.waze_status)
        _LOGGER.debug(("??Distances ...Waze    >>>, "
              "WazeFromHome=%s, WazeLastPollMoved=%s, WazeFromHomeMoved=%s, "
              "WazeTimeFmHome=%s"),
              waze_dist_from_home, waze_dist_last_poll_moved,
              waze_dist_from_home_moved, waze_time_from_home)
        _LOGGER.debug(("??Distances ...Calc    >>>, "
              "CalcFromHome=%s, CalcLastPollMoved=%s, CalcFromHomeMoved=%s"),
              calc_dist_from_home, calc_dist_last_poll_moved,
              calc_dist_from_home_moved)
   
        direction_info = ""
#        direction_info = " :: Zone={}, DistFmHome={}, LastDistFmHome={}, " \
#               "DistFmHomeMoved={}, DistLastPollMoved={}, Interval={}, " \
#               "Accur={}" \
#               .format(current_zone, dist_from_home, \
#               last_dist_from_home, dist_from_home_moved, \
#               dist_last_poll_moved, interval, gps_accuracy)
       
        direction_of_travel = ''
        if self.poor_gps_accuracy_flag.get(devicename):
            direction_of_travel = 'Poor.GPS'
        elif current_zone != 'not_home':
            direction_of_travel = 'in_zone'
            _LOGGER.debug("??Dir_of_Travel Setup 1>>>currZone != not_home")

        elif dist_from_home > self.zone_home_radius_near:
            if dist_from_home_moved <= -.3:            #.18 mi
                direction_of_travel = 'towards'
                _LOGGER.debug("??Dir_of_Travel Setup 5b>>>Towards")
            elif dist_from_home_moved >= .3:             #.18 mi
                direction_of_travel = 'away_from'
                _LOGGER.debug("??Dir_of_Travel Setup 5c>>dist>3=awayFrom")
            
            #Now check if stationary and override towards or away_from
            if dist_from_home > 3 and abs(dist_last_poll_moved) < .3:
                direction_of_travel = 'stationary'
                _LOGGER.debug("??Dir_of_Travel Setup 5a>>>stationary")
        else:
            direction_of_travel = 'near_home'
            _LOGGER.debug("??Dir_of_Travel Setup 6>>>near")
 
        direction_of_travel = direction_of_travel + direction_info
        
        _LOGGER.debug(("??Dir_of_Travel Determined >>>, "
                    "DirOfTrav=%s, LastDirOfTrav=%s, Accur=%s"),
                     direction_of_travel, last_dir_of_travel, gps_accuracy)

        _LOGGER.debug(("??SETUP_LOC_ATTRS <COMPLETE> ~~%s~~, "
                    "CurrentZone=%s, DistFmHome=%s, DistFmHomeMoved=%s, "
                    "DistLastPollMoved=%s"),
                    devicename, current_zone, dist_from_home,
                    dist_from_home_moved, dist_last_poll_moved)
 
        return (current_zone, direction_of_travel,
                dist_from_home, dist_from_home_moved, dist_last_poll_moved,
                waze_dist_from_home, calc_dist_from_home,
                waze_dist_from_home_moved, calc_dist_from_home_moved,
                waze_dist_last_poll_moved, calc_dist_last_poll_moved,
                waze_time_from_home)

#--------------------------------------------------------------------
    def _setup_info_attr(self, devicename, battery, gps_accuracy, \
                            stationary_cnt, dist_last_poll_moved, \
                            current_zone, location_isold_flag):

        """ Initialize info attribute with battery information
            Returns:
                - info 
        """

        if self.overrideinterval_seconds.get(devicename) > 0:
            info = '?Overriding.Interval'
        else:
            info = ''

        #Symbols = ????¦???????

        if gps_accuracy > int(self.gps_accuracy_threshold):
            info = '{} ?Poor.GPS.Accuracy-{}({})'.format(info, gps_accuracy,
                        self.poor_gps_accuracy_cnt.get(devicename))

        if current_zone == 'not_home' and dist_last_poll_moved > 0:
            info = '{} ?Traveled-{}{}'.format(info, dist_last_poll_moved,
                        self.unit_of_measurement)    

        if battery > 0:
            info = '{} ?Battery-{}%'.format(info, battery)

        if stationary_cnt > 2:
            info = '{} ?Stationary.Cnt-{}'.format(info, stationary_cnt)

        isold_cnt = self.location_isold_cnt.get(devicename)
        if isold_cnt > 0:
            info = '{} ?Old.Location-{}'.format(info, isold_cnt)

        if self.distance_method_waze_flag:
            if self.waze_status == WAZE_PAUSED:
                info = '{} ?Waze.Paused'.format(info)
            elif self.waze_status == WAZE_ERROR:
                info = '{} ?Waze.Error'.format(info)
            elif self.waze_status == WAZE_OUT_OF_RANGE:
                info = '{} ?Waze.Range-({}-{})'.format(info,
                            self._km_to_mi(self.waze_min_distance),
                            self._km_to_mi(self.waze_max_distance))

        return info
#--------------------------------------------------------------------
    def _retry_setup_location_data(self, device, devicename, location):
        """
        See if location data isOld=true. If so, sleep for 2 seconds
        and then get data from icloud again. Do this 5 times. If location
        isOld is still true, return to the update_data routine with
        the location data last found.
        """

        _LOGGER.debug("??RETRY_setup_location_data, ~~%s~~, Device=%s",
                devicename, device)

        location_retry_cnt = 0
        isold_flag = True
        while isold_flag and location_retry_cnt < 4:
            try:
                time.sleep(2)
                location_retry_cnt += 1
                status   = device.status(DEVICESTATUSSET)
                location = self.devices[devicename].location()
 #               location = status['location']
                isold_flag = location['isOld']
                if 'old' in self.debug_control: isold_flag = True     #debug
 
                _LOGGER.debug(("??RETRY_setup_location_data, ~~%s~~, "
                              "Timestamp=%s(%s), Next Update: %s(%s), "
                              "This poll: %s(%s), isOld=%s(%s), "
                              "Location=%s"),
                              devicename,
                              self._format_timestamp(location['timeStamp']),
                              location['timeStamp'],
                              self.next_update_time.get(devicename),
                              self.next_update_seconds.get(devicename),
                              self._seconds_to_time(self.this_update_seconds),
                              self.this_update_seconds,
                              location['isOld'], location_retry_cnt,
                              location)
            except:
                _LOGGER.debug(("??RETRY_setup_location_data-Unknown "
                              "Exception, Cnt=%s"), location_retry_cnt)
        return location

        
#########################################################
#
#   DEVICE SETUP SUPPORT FUNCTIONS
#
#########################################################


    def _check_tracking_this_device(self, devicename, device_type):
        ''' Validate device tracking via include/exclude filters '''

        # An entity will not be created by see() when track=false in
        # 'known_devices.yaml', but we need to see() it at least once

        entity_id = self._format_entity_id(devicename)

        #devicename in 'excluded_devices' parameter ==> Don't Track
        if devicename in self.exclude_devices:
            _LOGGER.info(("??Not Tracking %s, Did not pass"
                         " 'exclude_devices' filter (%s)"),
                         devicename, self.exclude_devices)
            return False

        #devicename in 'include_devices' parameter ==> Track
        elif devicename in self.include_devices:
            _LOGGER.info(("??Tracking %s, Passed"
                         " 'include_devices' filter (%s)"),
                         devicename, self.include_devices)
            return True

        #devicetype in 'include_device_types' parameter ==> Track
        elif device_type in self.include_device_types:
            _LOGGER.info(("??Tracking %s, Passed"
                         " 'include_device_type' filter (%s)"),
                         devicename, device_type)
            return True

        #devicetype in 'exclude_device_types' parameter ==> Don't Track
        elif device_type in self.exclude_device_types:
            _LOGGER.info(("??Not Tracking %s, Did not pass"
                         " 'exclude_device_types' filter (%s)"),
                         devicename, self.exclude_device_types)
            return False

        #neither 'include_device_types' nor 'exclude_device_types' parameter
        #and devicename not in 'include_devices' parameter    ==> Don't Track
        elif ('_xxx' in self.include_device_types and 
                '_xxx' in self.exclude_device_types and
                '_xxx' not in self.include_devices):
            _LOGGER.info(("??Not Tracking %s, No "
                         " 'include/exclude_device_types' filter (%s)"),
                         devicename, self.include_device_types)
            return False

        #'include_device_types parameter and 
        #devicename in 'exclude_device'                    ==> Don't Track
        elif ('_xxx' not in self.include_device_types and
                    devicename in self.exclude_devices):
            _LOGGER.info(("??Not Tracking %s, Did not pass"
                         " 'include_device_types' filter (%s)"),
                         devicename, self.include_device_types)
            return False

        #unknown device ==> Don't Track
        elif entity_id is None:
            _LOGGER.info("??Not Tracking %s, Unknown device", devicename)
            return False

        _LOGGER.info(("??Not tracking %s, Did not match any tracking ",
                    " filters, Type=%s"), devicename, device_type)
        return False
        
#--------------------------------------------------------------------
    def _check_isold_status(self, devicename, location_isold_flag,
                            time_stamp):
        """
        Check if the location isold flag is set by the iCloud service or if
        the current timestamp is the same as the timestamp on the previous
        poll. If so, we want to retry locating device
        5 times and then use normal interval. But keep track of count for
        determining the interval. 
        """
        isold_cnt = 0
        if 'old' in self.debug_control: location_isold_flag = True   #debug

        last_attrs       = self._get_device_attributes(devicename)
        last_time_stamp  = last_attrs[ATTR_LAST_LOCATED]

        location_isold_flag = (time_stamp == last_time_stamp)
        
        if location_isold_flag:
            isold_cnt = self.location_isold_cnt.get(devicename) + 1
            self.location_isold_cnt[devicename] = isold_cnt
 
            if isold_cnt % 5 == 0: location_isold_flag = False

        elif self.location_isold_cnt.get(devicename) > 0:
            self.location_isold_cnt[devicename] = 0

        return location_isold_flag, isold_cnt
#--------------------------------------------------------------------
    @staticmethod
    def _calculate_time_zone_offset():
        """ Calculate time zone offset seconds """
        try:
            local_zone_offset = dt_util.now().strftime('%z')
            local_zone_offset_seconds = int(local_zone_offset[1:3])*3600 + \
                        int(local_zone_offset[3:5])*60
            if local_zone_offset[:1] == "-":
                local_zone_offset_seconds = -1*local_zone_offset_seconds

            _LOGGER.debug(("??TIME ZONE OFFSET, Local Zone Offset: %s,"
                         " Seconds Offset: %s"),
                          local_zone_offset, local_zone_offset_seconds)
        except:
            local_zone_offset_seconds = 0

        return local_zone_offset_seconds
#--------------------------------------------------------------------
    @staticmethod
    def _interval_str_to_seconds(time_str='30 min'):
        """
        Calculate the seconds in the time string.
        The time attribute is in the form of '15 sec' ',
        '2 min', '60 min', etc
        """

        s1 = str(time_str).replace('_', ' ') + " min"
        time_part = float((s1.split(" ")[0]))
        text_part = s1.split(" ")[1]

        if text_part == 'sec':
            time = time_part
        elif text_part == 'min':
            time = time_part * 60
        elif text_part == 'hrs':
            time = time_part * 3600
        elif text_part == 'hr' or text_part == 'hrs':
            time = time_part * 3600
        else:
            time = 1200      #default to 20 minutes

        return time

#--------------------------------------------------------------------
    @staticmethod
    def _seconds_to_time_str(time):
        """ Create the time string from seconds """
        if time < 60:
            time_str = str(time) + " sec"
        elif time < 3600:
            time_str = str(round(time/60, 1)) + " min"
        elif time == 3600:
            time_str = "1 hr"
        else:
            time_str = str(round(time/3600, 1)) + " hrs"

        # xx.0 min/hr --> xx min/hr
        time_str = time_str.replace('.0 ', ' ')
        return time_str

#--------------------------------------------------------------------
    @staticmethod
    def _time_to_seconds(hhmmss):
        """ Convert hh:mm:ss into seconds """
        if hhmmss:
            s = hhmmss.split(":")
            tts_seconds = int(s[0]) * 3600 + int(s[1]) * 60 + int(s[2])
        else:
            tts_seconds = 0

        return tts_seconds

#--------------------------------------------------------------------
    def _km_to_mi(self, distance):
        return round(distance * self.km_mi_factor, 2)

    def _mi_to_km(self, distance):
        return round(distance / self.km_mi_factor, 2)

#--------------------------------------------------------------------
    @staticmethod
    def _calc_distance(from_lat, from_long, to_lat, to_long):
        d = round(distance(from_lat, from_long, to_lat, to_long) / 1000, 2)
        if d < .05: d = 0
        return d

#--------------------------------------------------------------------
    @staticmethod
    def _round_to_zero(distance):
        if distance < .05: distance = 0
        return round(distance, 2)

#--------------------------------------------------------------------
    def _get_waze_data(self, this_lat, this_long, last_lat, last_long,
                            current_zone, last_dist_from_home):

        if current_zone == 'home':
            return (WAZE_USED, 0, 0, 0)
        elif self.waze_status == WAZE_PAUSED:
            return (WAZE_PAUSED, 0, 0, 0)
            
        #Last distance outside of Waze outside of range
#        elif (last_dist_from_home >= self.waze_max_distance) or \
#             (last_dist_from_home <= self.waze_min_distance):
#            return (WAZE_OUT_OF_RANGE,0, 0, 0)

        waze_from_home = self._get_waze_distance(this_lat, this_long, 
                            self.zone_home_lat, self.zone_home_long)
        
        waze_from_last_poll = self._get_waze_distance(last_lat, last_long, 
                            this_lat, this_long)
        
        waze_status         =  waze_from_home[0]
        waze_dist_from_home = self._round_to_zero(waze_from_home[1])
        waze_time_from_home = self._round_to_zero(waze_from_home[2])
        waze_dist_last_poll = self._round_to_zero(waze_from_last_poll[1])

        if waze_dist_from_home == 0:
            waze_time_from_home = 0
        else:
            waze_time_from_home = self._round_to_zero(waze_from_home[2])
            
        if ((waze_dist_from_home > self.waze_max_distance) or
             (waze_dist_from_home < self.waze_min_distance)):
 
            waze_status = WAZE_OUT_OF_RANGE

        _LOGGER.debug(("??Waze distances calculated >>>, "
          "Status=%s, DistFromHome=%s, TimeFromHome=%s, "
          " DistLastPoll=%s, "
          "WazeFromHome=%s, WazeFromLastPoll=%s"),
          waze_status, waze_dist_from_home, waze_time_from_home,
          waze_dist_last_poll, waze_from_home, waze_from_last_poll)

        return (waze_status, waze_dist_from_home, waze_time_from_home,
                waze_dist_last_poll)

#--------------------------------------------------------------------
    def _get_waze_distance(self, from_lat, from_long, to_lat, to_long):
        """
        See https://github.com/kovacsbalu/WazeRouteCalculator
        Region=EU (Europe), US or NA (North America), IL (Israel)

        Example:
            from_address = 'Budapest, Hungary'
            to_address = 'Gyor, Hungary'
            region = 'EU'
            route = WazeRouteCalculator.WazeRouteCalculator(from_address, to_address, region)
            route.calc_route_info()
            route_time, route_distance = route.calc_route_info()
        
        Example output:
            From: Budapest, Hungary - to: Gyor, Hungary
            Time 72.42 minutes, distance 121.33 km.
            (72.41666666666667, 121.325)

        See https://github.com/home-assistant/home-assistant/blob
        /master/homeassistant/components/sensor/waze_travel_time.py
        """
        
        try:
            from_loc = '{},{}'.format(from_lat, from_long)
            to_loc = '{},{}'.format(to_lat, to_long)
            
            route = WazeRouteCalculator.WazeRouteCalculator(
                    from_loc, to_loc, self.waze_region)
            
            route_time, route_distance = \
                    route.calc_route_info(self.waze_realtime) 
  
            route_time = round(route_time, 0)
            route_distance +- self.waze_adjustment
            route_distance = round(route_distance, 2)
           
            return (WAZE_USED, route_distance, route_time, route)
            
        except WazeRouteCalculator.WRCError as exp:
            _LOGGER.error("??Error on retrieving data: %s", exp)
            return (WAZE_ERROR, 0, 0, 0)
            
        except KeyError:
            _LOGGER.error("??Error retrieving data from server")
            return (WAZE_ERROR, 0, 0, 0)
#--------------------------------------------------------------------
    def _format_waze_time_msg(self, devicename, waze_time_from_home,
                                waze_dist_from_home):
        """ return the message displayed in the waze time field ??   """

        if (waze_dist_from_home == 0 or 
                    self.waze_status == WAZE_NOT_USED or
                    self.waze_status == WAZE_PAUSED):
            waze_time_msg = ''
        elif self.poor_gps_accuracy_flag.get(devicename):
            waze_time_msg = '?BADGPS?'
        elif self.waze_status == WAZE_OUT_OF_RANGE:
            waze_time_msg = '?RANGE?'
        elif self.waze_status == WAZE_USED:   #Waze used on this poll
            
            #Display time to the nearest minute if more than 3 min away
            t = waze_time_from_home * 60
            r = 0
            if t > 180:
              t, r = divmod(t, 60)
              t = t + 1 if r > 30 else t
              t = t * 60

            waze_time_msg = self._seconds_to_time_str(t)
                    
        elif self.waze_status == WAZE_ERROR:
            waze_time_msg = '?ERROR?'

        return waze_time_msg
#--------------------------------------------------------------------
    def _seconds_to_time(self, seconds):
        """ Convert seconds to hh:mm:ss """
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        if self.unit_of_measurement == 'mi' and h > 12:
            h = h - 12
        h = 12 if h == 0 else h

        return "%d:%02d:%02d" % (h, m, s)

#--------------------------------------------------------------------
    def _format_timestamp(self, utc_timestamp):
        """
        Convert iCloud timeStamp into the local time zone and
        return hh:mm:ss
        """

        ts_local = int(float(utc_timestamp)/1000) + \
                self.time_zone_offset_seconds
        ts_str = dt_util.utc_from_timestamp(
                ts_local).strftime(self.time_format)
        if ts_str[0] == "0":
            ts_str = ts_str[1:]
        return ts_str

#--------------------------------------------------------------------
    def _add_comma_to_str(self, text):    
        """ Add a comma to info if it is not an empty string """
        if text: 
            return '{}, '.format(text)
        return ''
#########################################################
#
#   ICLOUD ROUTINES
#
#########################################################

    def lost_iphone(self, devicename):
        """Call the lost iPhone function if the device is found."""
        if self.api is None:
            return

        self.api.authenticate()

        for device in self.api.devices:
            if devicename is None or device == self.devices[devicename]:
                device.play_sound()

#--------------------------------------------------------------------
    def update_icloud(self, arg_devicename=None, arg_command=None):
        """
        Authenticate against iCloud and scan for devices.
        
        Commands:
        - waze reset range = reset the min-max rnge to defaults (1-1000)
        - waze toggle      = toggle waze on or off
        - pause            = stop polling for the devicename or all devices
        - resume           = resume polling devicename or all devices, reset
                             the interval override to normal interval 
                             calculations
        - pause-resume     = same as above but toggles between pause and resume 
        - zone xxxx        = updates the devie state to xxxx and updates all
                             of the iloud3 attributes. This does the see
                             service call and then an update.
        - reset            = reset everything and rescans all of the devices 
        - debug interval   = displays the interval formula being used
        - debug gps        = simulates bad gps accuracy
        - debug old        = simulates that the location informaiton is old
        """
        
        from pyicloud.exceptions import PyiCloudNoDevicesException

        if self.api is None:
            return
            
        arg_command        = "{} x".format(arg_command)
        arg_command_cmd    = arg_command.split(' ')[0].lower()
        arg_command_parm_z = arg_command.split(' ')[1]       #original value
        arg_command_parm   = arg_command_parm_z.lower()
        
        _LOGGER.debug(("??UPDATE ICLOUD COMMAND - UPDATE BEGIN  "
                "DeviceArg={}, CommandArg=%s, CommandPart=%s, ParmPart=%s/"),
                arg_devicename, arg_command_cmd, arg_command_parm)

        if arg_command_cmd == 'waze':   #and self.distance_method_waze_flag: 
            if arg_command_parm == 'reset_range':
                self.waze_min_distance = 0
                self.waze_max_distance = 99999
                self.waze_status  = WAZE_USED
            elif self.waze_status == WAZE_USED:
                self.waze_status  = WAZE_PAUSED
            else:
                self.waze_status = WAZE_USED
 
        elif arg_command_cmd == 'zone':     #parmeter is the new zone
            if 'home' in arg_command_parm_z:    #home/not_home is lower case
                arg_command_parm_z = arg_command_parm
        
            kwargs = {}
            attrs  = {}

            self.last_state[arg_devicename] = arg_command_parm_z
            self._update_device_attributes(arg_devicename, kwargs, attrs)
            self._update_all_devices(arg_devicename)    
            self.update_inprocess_flag = False
            return
        
        elif arg_command_cmd == 'reset':
            self.reset_account_icloud()
            return
 
#       loop through all devices being tracked and
#       update the attributes. Set various flags if pausing or resuming
#       that will be processed by the next poll in '_device_polling_15_sec_timer_loop'
        devs = [arg_devicename] if arg_devicename else self.devices
        device_time_adj = 0
        for devicename in devs:
            device_time_adj += 3
            
            #An update is in process, must wait until done
            while self.update_inprocess_flag:
                now_seconds = dt_util.now().strftime('%-S')
                attrs                = {}
                attrs[CONF_INTERVAL] = "?WAIT-{}?".format(now_seconds)

                kwargs = {}
                self._update_device_attributes(devicename, kwargs, attrs)
                time.sleep(2)

            now_seconds = self._time_to_seconds(dt_util.now().strftime('%X'))
            x, update_in_secs = divmod(now_seconds, 15)
            update_in_secs = 15 - update_in_secs + device_time_adj

            if arg_devicename is None or \
                (arg_devicename and arg_devicename == devicename):

                attrs = {}

                if arg_command_cmd == 'debug':
                    arg_command_cmd = 'resume'      #force restart for changes
                    if arg_command_parm in self.debug_control:
                        self.debug_control = \
                                self.debug_control.replace(arg_command_parm,'')
                        self.debug_control = \
                                self.debug_control.replace(',,',',')
                    else:
                        self.debug_control = '{},{}'.format(\
                                self.debug_control, arg_command_parm)
                    attrs[ATTR_INFO] = '? {} ?'.format(self.debug_control)
                                            
                if arg_command_cmd == 'pause-resume':
                    if self.next_update_time[devicename] == 'Paused':
                        arg_command_cmd = 'resume'
                    else:
                        arg_command_cmd = 'pause'
                        
                if arg_command_cmd == 'pause':
                    cmd_type = CMD_PAUSE
                    self.next_update_seconds[devicename] = 99999
                    self.next_update_time[devicename]    = 'Paused'
                    attrs[CONF_INTERVAL]                 ='?PAUSE?'

                elif arg_command_cmd == 'resume':
                    cmd_type = CMD_RESUME
                    self.next_update_time[devicename]         = '00:00:00'
                    self.next_update_seconds[devicename]      = 0
                    self.overrideinterval_seconds[devicename] = 0
                    attrs[ATTR_NEXT_UPDATE_TIME]              = '00:00:00'
                    attrs[CONF_INTERVAL]  = '?GO-{}s?'.format(update_in_secs)
      
                elif arg_command_cmd == 'waze':
                    cmd_type = CMD_WAZE
                    if self.next_update_time[devicename] != 'Paused':
                        self.next_update_time[devicename]         = '00:00:00'
                        self.next_update_seconds[devicename]      = 0
                        self.overrideinterval_seconds[devicename] = 0
                        attrs[ATTR_NEXT_UPDATE_TIME]              = '00:00:00'
                        
                    if self.waze_status == WAZE_PAUSED:
                        attrs[ATTR_WAZE_TIME] = ''      #?WAZEOFF?'
                    elif self.next_update_time[devicename] == 'Paused':
                        attrs[ATTR_WAZE_TIME] = ''
                    else:
                        attrs[ATTR_WAZE_TIME] = '?GO-{}s'.\
                                                format(update_in_secs)
                    
                else:
                    cmd_type = CMD_ERROR
                    attrs[ATTR_INFO] = '? INVALID COMMAND ({}) ?'.\
                                                format(arg_command)

                kwargs = {}
                self._update_device_attributes(devicename, kwargs, attrs)
                
            #end if arg_devicename =none or devicename statement
        #end for devicename in devs loop           
            
        _LOGGER.debug(("??UPDATE ICLOUD COMMAND - UPDATE END %s "
                        "Attributes=%s"), devicename, attrs)
                        
        _LOGGER.debug("??UPDATE ICLOUD COMMAND - End")


#--------------------------------------------------------------------
    def setinterval(self, arg_interval=None, arg_devicename=None):
        """
        Set the interval or process the action command of the given devices.
            'interval' has the following options:
                - 15               = 15 minutes
                - 15 min           = 15 minutes
                - 15 sec           = 15 seconds
                - 5 hrs            = 5 hours
                - Pause            = Pause polling for all devices
                                     (or specific device if devicename
                                      is specified)
                - Resume            = Resume polling for all devices
                                     (or specific device if devicename
                                      is specified)
                - Waze              = Toggle Waze on/off
        """

        devs = [arg_devicename] if arg_devicename else self.devices

        if arg_interval is not None:
            cmd_type = CMD_INTERVAL
            new_interval = arg_interval.lower().replace('_', ' ')
        
#       loop through all devices being tracked and
#       update the attributes. Set various flags if pausing or resuming
#       that will be processed by the next poll in '_device_polling_15_sec_timer_loop'
        device_time_adj = 0
        for devicename in devs:
            device_time_adj += 3

            #An update is in process, must wait until done
            while self.update_inprocess_flag:
                now_seconds = dt_util.now().strftime('%-S')
                attrs                = {}
                attrs[CONF_INTERVAL] = "?WAIT-{}?".format(now_seconds)

                kwargs = {}
                self._update_device_attributes(devicename, kwargs, attrs)
                time.sleep(2)

            _LOGGER.debug(("??SET INTERVAL COMMAND Start %s, "
                          "ArgDevname=%s, ArgInterval=%s"
                          "Old/New Interval: %s/%s"),
                          devicename, arg_devicename, arg_interval,
                          self.interval_str.get(devicename), new_interval)

            if (arg_devicename is None or
              (arg_devicename and arg_devicename == devicename)):

                self.next_update_time[devicename]         = '00:00:00'
                self.next_update_seconds[devicename]      = 0
                self.overrideinterval_seconds[devicename] = 0

                self.interval_str[devicename] = new_interval
                self.overrideinterval_seconds[devicename] = \
                        self._interval_str_to_seconds(new_interval)
                        
                now_seconds = \
                    self._time_to_seconds(dt_util.now().strftime('%X'))
                x, update_in_secs = divmod(now_seconds, 15)
                time_suffix = 15 - update_in_secs + device_time_adj
                               
                kwargs = {}
                attrs  = {}
                attrs[CONF_INTERVAL] = "?GO-{}?".format(time_suffix)
                                            
                self._update_device_attributes(devicename, kwargs, attrs)

                _LOGGER.debug("??SET INTERVAL COMMAND END %s", devicename)

#--------------------------------------------------------------------
