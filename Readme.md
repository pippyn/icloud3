# iCloud3  Device Tracker Custom Component  

[![Version](https://img.shields.io/badge/Version-0.85-blue.svg "Version")](https://github.com/gcobb321/icloud3)
[![Released](https://img.shields.io/badge/Released-1/31/2019-brightgreen.svg "Released")](https://github.com/gcobb321/icloud3)
[![Project Stage](https://img.shields.io/badge/ProjectStage-Development-yellow.svg "Project Stage")](https://github.com/gcobb321/icloud3)
[![Type](https://img.shields.io/badge/Type-CustomComponent-yellow.svg "Type")](https://github.com/gcobb321/icloud3)
[![Licensed](https://img.shields.io/badge/Licesned-MIT-green.svg "License")](https://github.com/gcobb321/icloud3)

----------

iCloud3 is an improved version of the iCloud device_tracker component installed with Home Assistant.  
  
It is installed as a custom device_tracker component in the config/custom_component/device_tracker directory. Instructions are found at the end of this document. 

## INTRODUCTION

### What's different

iCloud3 has many features not in the base iCloud device_tracker that is part of Home Assistant. It exposes many new attributes, provides many new features, is based on enhanced route tracking methods, is much more accurate, and includes additional service calls. Lets look at the differences.

| Feature | original iCloud | iCloud3 |
|---------|-----------------|---------|
| Device Selection | None | Include and/or exclude device by type (iPhone, iPad, etc) or by device name (garyiphone, lillianiphone, etc) |
| Minimum Poll Interval | 1 minute | 15 second |
| Distance Accuracy | 1 km/mile | .01 km/mile |
| Hide location if not in a zone | No | Yes |
| Variable Polling | Yes - Based on distance from home, battery level, GPS Accuracy | Yes - Based on distance from home, Waze travel time to home, direction of travel, if the device is in a zone, battery level, GPS Accuracy, 'old location' status |
| Detects zone changes | No - Also requires other device_trackers (OwnTracks, Nmap, ping, etc. | Yes - No other programs are needed |
| Detects when leaving Home Zone | Delayed to next poll | Automatic |
| Fixes 'Not Home' issue when in Sleep Mode | No | Yes, on next 15-second cycle |
| Integrates with Waze route/map tracker | No | Yes - Uses Waze travel time to home |
| Device Poll Interval when close to home | 1 minute | 15-seconds |
| Dynamic Stationary Zone | No | Yes |
| Service call commands | Set polling interval, Reset devices | Set polling interval, Reset devices, Pause/restart polling, Change zone, Enable/disable Waze Route information usage (some commands can be for all devices or for a specific device) |
| Device Filters | None | By device type or device name |
| Number of Configuration variables available | 5 | 21 |
| Number of Attribute variables returned | 20 | 33 |
| Number of Service Call | 4  | 4 + 10 special commands |
 
### How it works

iCloud3 polls the device on a dynamic schedule and determines the polling interval time based on:
 - If the device in a zone or not in a zone. The zones include the ones you have set up in zone.yaml and a special Dynamic Stationary Zone that is created by iCloud3 when you haven't changed your location in a while (shopping center, friends house, doctors office, etc.)
 - A 'line-of-sight' calculated distance from 'home' to your current location using the GPS coordinates.
 - The driving time and distance between 'home' and your current location using the [Waze](http://www.waze.com) map/driving/direction service. 
 - The direction you are going — towards home, away from home or stationary.
 - The battery level of the device.
 - The accuracy of the GPS location and if the last poll returned a location that the iCloud service determined was 'old'.
  
The above analysis results in a polling interval. The further away from home and the longer the travel time back to home, the longer the interval; the closer to home, the shorter the interval. The polling interval checks each device being tracked every 15 seconds to see if it's location should be updated. If so, it and all of the other devices being tracked with iCloud3 are updated (more about this below). With a 15 second interval, you track the distance down 1/10 of a mile/kilometer. This gives a much more accurate distance number that can used to trigger automations. You no longer limited to entering or exiting a zone. 

Note: The `pyicloud.py` Python component is part of Home Assistant and used to poll the device, requesting location and other information. If the iCloud account is associated with multiple devices, all of the devices are polled, whether or not the device is being tracked by Home Assistant. This is a limitation of pyicloud.py. 


### What other programs do I need

The `Home Assistant IOS App` is all. You do not need `OwnTracks` or other location based trackers and you do not need `nmap`, `netgear`, `ping` or any network monitor. The `Home Assistant IOS App` will notify Home Assistant when you leave home and iCloud3 device tracker will start keeping up with the device's location, the distance to home and the time it will take to get there.  
   
*Note:* The IOS App settings `Zone enter/exit`, `Background fetch` and `Significant location change` location settings need to be enabled. 


The `iCloud` platform allows you to detect presence using the  [iCloud](https://www.icloud.com/) service. iCloud allows users to track their location on iOS devices. Your device needs to be registered with “Find My iPhone”.
  
  
### Home Assistant Configuration

To integrate iCloud in Home Assistant, add the following section to your `configuration.yaml` file:

```
# Example configuration.yaml entry
device_tracker:
  - platform: icloud3
    username: USERNAME 
    password: PASSWORD
    account_name: accountname
    include_device_type: iphone

```

### About Your Apple iCloud Account
  
Apple has enabled '2 Step Authentication' for iCloud accounts. To permit Home Assistant, and iCloud3, to access your iCloud account,  you need to have an authentication code sent via a text message to a trusted device, which is then entered in Home Assistant. The duration of this authentication is determined by Apple, but is now at 2 months.  
  
*Note:* `pyicloud`, the Python program used to access your iCloud account, does not support 2 Factor Authentication, the improved version of 2 Steps Authentication.

When your account needs to be authorized, or reauthorized, you will be notified and the Notification symbol (the bell in the upper right of the Home Assistant screen) will be highlighted. Take the following steps to complete the process:  
  1. Press the Notification Bell.
  2. A window is displayed, listing the trusted devices associated with your account. It will list an number (0, 1, 2, etc.) next to the phone number that can receive the text message containing the 2 Step Authentication code number used to authenticate the computer running Home Assistant (your Raspberry Pi for example).
  3. Type the number.
  4. A text message is sent. Type the authentication code you receive in the next window that is displayed.
  
**Associating the iPhone Device Name with Home Assistant using the Home Assistant IOS App**   
The Device Name field of the device in Settings App>General>About>Name field on the iPhone and iPad and in the Apple Watch App for the iWatch is stored in the iCloud account and used by Home Assistant to identify the device. HA v0.86+ converts any secial characters found in the Device Name field to an underscore ( _ ) while HA v0.85 and earlier droped the special caracters altogether; e.g., 'Gary-iPhone' becomes 'gary_iphone' in known_devices.yaml, automations, sensors, scripts, etc. The value, 'gary_iphone', in the Device ID field in the Home Assistant IOS App>Settings ties everything together. 
  
*Note:* When you use iCloud account is accessed on a new device, you may receive an email from Apple stating that someone has logged into your account.  
  
 


## CONFIGURATION VARIABLES

**username**  
*(Required)* The username (email address) for the iCloud account. 

**password**  
*(Required)* The password for the account.

**account_name**  
The friendly name for the account_name.  
*Note:* If this isn’t specified, the account_name part of the username (the part before the `@` in the email address) will be used.

**include_device_types**  (or  **include_device_type**)  
**exclude_device_types**  (or  **exclude_device_type**)  
Include or exclude device type(s) that should* be tracked.  
*Default: Include all device types associated with the account*

```
# Example yaml
include_device_type: iphone

# Example yaml
include_device_types:
  - iphone
  - ipad
```

**include_devices**  (or  **include_device**)  
**exclude_devices**  (or  **exclude_device**)  
Include or exclude devices that should be tracked.  
*Default: Include all devices associated with the account*  

```
# Example yaml
include_device_type:
  - iphone
exclude_device:
  - gary_iphone
```  

*Note:* It is recommended that to you specify the devices or the device types you want to track to avoid confusion or errors. All of the devices you are tracking are shown in the `devices_tracked ` attribute.  

**inzone_interval**  
The interval between location upates when the device is in a zone. This can be in seconds, minutes or hours, e.g., 30 secs, 1 hr, 45 min, or 30 (minutes are assumed if no time qualifier is specified).  
*Default: 2 hrs*

**gps_accuracy_threshold**  
iCloud location updates come with some gps_accuracy varying from 10 to 5000 meters. This setting defines the accuracy threshold in meters for a location updates. This allows more precise location monitoring and fewer false positive zone changes. If the gps_accuracy is above this threshold, a location update will be retried again in 2 minutes to see if the accuracy has improved. After 5 retries, the normal interval that is based on the distance from home, the waze travel time and the direction will be used.  
*Default: 1000*

*Note:* The accuracy and retry count are displayed in the `info` attribute field (*GPS.Accuracy-263(2)*) and on the `poll_count`  attribute field (*2-GPS*). In this example, the accuracy has been poor for 2 polling cycles.  

**hide_gps_coordinates**
Hide the latitude and longitude of the device if not in a zone. 
*Note: This option provided enhanced security by only reporting the devices location when it is in a zone.*
*Valid values: True, False. Default: False* 

**unit_of_measurement**  
The unit of measure for distances in miles or kilometers.   
*Valid values: mi, km. Default: mi*
 
**distance_method**  
iCloud3 uses two methods of determining the distance between home and your current location — by calculating the straight line distance using geometry formulas (like the Proximity sensor) and by using the Waze Route Tracker to determine the distance based on the driving route.   
*Valid values: waze, calc. Default: waze*  
  
*Note:* The Waze distance becomes less accurate when you are close to home. The calculation method is used at distances less than 1 mile or 1 kilometer.  
  
**waze_min_distance, waze_max_distance**  
These values are also used to determine if the polling internal should be based on the Waze distance. The calculated distance must be between these values for the Waze distance to be used.  
*Default: min=0, max=1000*  

*Note:* If you are a long way from home, it probably doesn't make sense to use the Waze distance. You probably don't have any automations that would be triggered from that far away. 
  
**waze_real_time**  
Waze reports the travel time estimate two ways — by taking the current, real time traffic conditions into consideration (True) or as an average travel time for the time of day (False).  
*Valid values: True, False. Default: False*  
  
**waze_region**  
The area used by Waze to determine the distance and travel time.  
*Valid values: US (United States), NA (North America), EU (Europe), IL (Isreal). Default: US*  
  
**travel_time_factor**  
When using Waze and the distance from your current location to home is more than 3 kilometers/miles, the polling interval is calculated by multiplying the driving time to home by the `travel_time_factor`.  
*Default: .75*  

*Note:* Using the default value, the next update will be 3/4 of the time it takes to drive home from your current location. The one after that will be 3/4 of the time from that point. The result is a smaller interval as you get closer to home and a larger one as you get further away.  
 
## SPECIAL ZONES  
  
There are two zones that are special to the iCloud3 device tracker - the Dynamic Stationary Zone and the NearZone zone.

**Dynamic Stationary Zone**  
When a device has not moved for 600m/200ft in 2 polling cycles, it is considered to be stationary. Examples might be when you are at a mall, doctor's office, restaurant, friend's house, etc. If the device is stationary, it's Stationary Zone location (latitude and longitude) is automatically updated with the current values, the device state is changed and the interval time is set to the *inzone_interval* value (default is 2 hrs). This almost eliminates the number of times the device must be polled to see how far it is from home when you haven't moved for a while. When you leave the Stationary Zone, the IOS App notifies Home Assistant that the Stationary Zone has been exited and the device tracking begins again.

*Note:* You do not have to create the Stationary Zone in the zones.yaml file, the iCloud3 device tracker automatically creates one for every device being tracked when Home Assistant is started. It's name is *devicename_Stationary*.  
  
**NearZone Zone**  
There may be times when the Home Zone's (or another zone's) cell service is poor and does not track the device adequately when the device nears a zone. This can create problems triggering automations when the device enters the zone since the Find-My-Friends location service has problems monitoring it's location.  
  
To solve this, a special 'NearZone' zone can be created that is a short distance from the real zone that will wake the device up. The IOS App stores the zone's location on the device and will trigger a zone enter/exit notification which will then change the device's device_tracker state to the NearZone zone and change the polling interval to every 15-secs. It is not perfect and might not work every time but it is better than utomations never being triggered when they should.
  
*Note:* You can have more than one NearZone zone in the zones.yaml file. Set them up with a unique name that starts with NearZone;, e.g., NearZone-Home, NearZone-Quail, NearZone-Work, etc. The *friendly_name* attribute should be NearZone for each one.

## ATTRIBUTES

There are numerous attributes that are available for use in automations or to monitor the location of your device. They are shown in following table.  

**battery**  
The battery level of the device..  
  
**authenticated**  
When the device's iCloud account was last authenticated.  
  
**interval**  
The current interval between update requests to your iCloud account for the location and other information. They increase as you get further away and decrease as you get closer to home.  
  
**travel_time**  
The Waze travel time to return home from your current location.  
  
**distance**  
The distance from home being used by the interval calculator. This will be either the Waze distance or the calculated distance.  
  
**waze_distance**  
The driving distance from home returned by Waze based on the shortest route.  
  
**calculated_distance**  
The 'straight line' distance that is calculated using the latitude and longitude of home and your current location using geometric formulas.  
  
**dir_of_travel**  
The direction you are traveling — towards home, away from home, near home, or stationary. This is determined by calculating the difference between the distance from home on this location update and the last one. Stationary can be a little difficult to determine at times and sometimes needs several updates to get right.  
  
**last_located**  
The last time your iCloud account successfully located the device. Normally, this will be a few seconds after the update time, however, if you are in a dead zone or the GPS accuracy exceeds the threshold, the time will be older. In this case, a description of the issues is displayed in the `info` attribute field.  
  
**last_update**  
The time of the last iCloud location update.  
  
**next_update**  
The time of the next iCloud location update.  
  
**poll_count**  
The number of iCloud location updates done that day.  
  
**info**  
A message area displaying information about the device. This includes the battery level, Waze status, GPS accuracy issues, how long the device has been stationary, etc.  
  
**tracked_devices**  
The devices that are being tracked based on the 'includes' and 'excludes' specified in the configuration.yaml file.  This will be the same for all devices tracked.  
  
**device_status**  
The status of the device — online if the device is located or offline if polling has been paused or it can not be located.  
  
**battery_status**  
Charging or NotCharging.  
  
**latitude, longitude, altitude**  
The location of the device.  
  
**source_type**  
How the the `Home Assistant IOS App` located the device. This includes gps, beacon, router.  
  
## Accessing Attributes in Automations and in Lovelace

Automations can access the attribute's value using the `states.attributes.attributename` statement. The third trigger in the example below will trigger the `gary_arrives_home` automation when the distance goes below .25.  

```
# Example yaml (automation.yaml)
- alias: gary_arrives_home
  trigger:
 
    - platform: state
      entity_id: device_tracker.gary_iphone
      to: 'home
      
    - platform: numeric_state
      entity_id: device_tracker.gary_iphone
      value_template: '{{float(state.attributes.distance)}}'
      below: .21

```  
  
An entity's state can be displayed on a Lovelace card but the attribute's value cannot. To display the attribute's value, a sensor template can be used that will be updated when the attribute's value changes. The following example will display the `distance` attribute.  
  
```
# Example yaml (sensor.yaml)
- platform: template
  sensors:
    gary_iphone_distance:
      value_template: '{{float(state_attr("device_tracker.gary_iphone","distance"))}}'
      unit_of_measurement: 'mi'

```

And on a Lovelace card:
```
# Example yaml
- entity: sensor.gary_iphone_distance
  name: Distance
  icon: mdi:map-marker-distance 

```
  
*Note:* It is better to access the attribute's value in automation rather than using a template sensor. The reason is that when the attribute changes value, it will trigger the automation immediately. If the template sensor is used, the automation becomes a two step process; the sensor must be changed before the automation will be triggered.  
  
## DEVICE TRACKER SERVICES 
  
Four services are available for the iCloud3 device tracker component that are used in automations. 

| Service | Description |
|---------|-------------|
| icloud_update | Send commands to iCloud3 that change the way it is running (pause, resume, Waze commands, etc.) |
| icloud_set_interval | Override the dynamic interval calculated by iCloud3. |
| icloud_lost_phone | Play the Lost Phone sound. |
| icloud_reset | Reset the iCloud3 custom component. |

Description of each service follows.
  
### SERVICE — icloud_update
This service allows you to change the way iCloud3 operates. The following parameters are used:

| Parameter | Description |
|-----------|-------------|
| account_name | account_name of the iCloud3 custom component specified in the Configuration Variables section described at the beginning of this document. *(Required)*|
| device_name | Name of the device to be updated. All devices will be updated if this parameter is not specified. *(Optional)* |
| command | The action to be performed (see below). *(Required)* |
| parameter | Additional parameters for the command. |
  
The following describe the commands that are available. 
  
| Command |  Parameter | Description |
|---------|------------|-------------|
| pause |  | Stop updating/locating a device (or all devices). Note: You may want to pause location updates for a device if you are a long way from home or out of the country and it doesn't make sense to continue locating your device. |
| resume |  | Start updating/locating a device (or all devices) after it has been paused. |  
| resume |  | Reset the update interval if it was overridden the 'icloud_set_interval' service. |
| pause-resume |  | Toggle pause and resume commands |
| zone | zonename | Change iCloud3 state to 'zonename' (like the device_tracker.see service call) and immediately update the device interval and location data. Note: Using the device_tracker.see service call instead will update the device state but the new interval and location data will be delayed until the next 15-second polling iteration (rather than immediately). |
| waze | on | Turn on Waze. Use the 'waze' method to determine the update interval. |
| waze | off | Turn off Waze. Use the 'calc' method to determine the update interval. |
| waze | toggle | Toggle waze on or off |
|  waze | reset_range | Reset the Waze range to the default distances (min=1, max=99999). |
| debug | interval | Show how the interval is determined by iCloud3. This is displayed real time in the `info` attribute field. |
  

```
#Example Automations.yaml
icloud_command_pause_resume_polling:
  alias: 'Toggle Pause/Resume Polling'
  sequence:
    - service: device_tracker.icloud_update
      data:
        account_name: gary_icloud
        command: pause-resume
 
icloud_command_resume_polling:
  alias: 'Resume Polling'
  sequence:
    - service: device_tracker.icloud_update
      data:
        account_name: gary_icloud
        command: resume
        
icloud_command_pause_polling:
  alias: 'Pause Polling'
  sequence:
    - service: device_tracker.icloud_update
      data:
        account_name: gary_icloud
        command: pause

icloud_command_pause_polling_gary:
  alias: 'Pause (Gary)'
  sequence:
    - service: device_tracker.icloud_update
      data:
        account_name: gary_icloud
        device_name: gary_iphone
        command: pause

icloud_command_toggle_waze:
  alias: 'Toggle Waze On/Off'
  sequence:
    - service: device_tracker.icloud_update
      data:
        account_name: gary_icloud
        command: waze toggle

icloud_command_garyiphone_zone_home:
  alias: 'Gary - Zone Home'
  sequence:
    - service: device_tracker.icloud_update
      data:
        account_name: gary_icloud
        device_name: gary_iphone
        command: zone home
        
icloud_command_garyiphone_zone_not_home:
  alias: 'Gary - Zone not_home'
  sequence:
    - service: device_tracker.icloud_update
      data:
        account_name: gary_icloud
        device_name: gary_iphone
        command: zone not_home
```

  
### SERVICE — icloud_set_interval  
This service allows you to override the interval between location updates to a fixed time. It is reset when a zone is entered or when the icloud_update service call is processed with the 'resume'command. The following parameters are used:

| Parameter | Description |
|-----------|-------------|
| account_name | account_name of the iCloud3 custom component specified in the Configuration Variables section described at the beginning of this document. *(Required)* |
| device_name | Name of the device to be updated. All devices will be updated if this parameter is not specified. *(Optional)* |
| interval | The interval between location updates. This can be in seconds, minutes or hours. Examples are 30 sec, 45 min, 1 hr,  hrs, 30 (minutes are assumed if no time descriptor is specified). *(Required)* |

```
#Example Automations.yaml           
icloud_set_interval_15_sec_gary:
  alias: 'Set Gary to 15 sec'
  sequence:
    - service: device_tracker.icloud_set_interval
      data:
        account_name: gary_icloud
        device_name: gary_iphone
        interval: '15 sec'
 
icloud_set_interval_1_min_gary:
  alias: 'Set Gary to 1 min'
  sequence:
    - service: device_tracker.icloud_set_interval
      data:
        account_name: gary_icloud
        device_name: gary_iphone
        interval: 1

icloud_set_interval_5_hrs_all:
  alias: 'Set interval to 5 hrs (all devices)'
  sequence:
    - service: device_tracker.icloud_set_interval
      data:
        account_name: gary_icloud
        interval: '5 hrs'
 
```
  
### SERVICE — icloud_lost_iphone 
This service will play the Lost iPhone sound on a specific device. 

| Parameter | Description |
|-----------|-------------|
| account_name | account_name of the iCloud3 custom component specified in the Configuration Variables section described at the beginning of this document. *(Required)* |
| device_name | Name of the device *(Required)* |
  
### SERVICE — icloud_reset
This service will refresh all of the devices being handled by iCloud3 and can be used when you have added a new device to your Apple account. You will have to restart Home Assist if you have made changes to the platform parameters (new device type, new device name, etc.) 
  
| Parameter | Description |
|-----------|-------------|
| account_name | account_name of the iCloud3 custom component specified in the Configuration Variables section described at the beginning of this document. *(Required)* |
  
  
## TECHNICAL INFORMATION - HOW THE INTERVAL IS DETERMINED
The iCloud3 device tracked uses data from several sources to determine the time interval between the iCloud Find my Friends location update requests.  The purpose is to provide accurate location data without exceeding Apple's limit on the number of requests in a time period and to limit the drain on the device's battery.

The algorithm uses a sequence of tests to determine the interval. If the test is true, it's interval value is used and no further tests are done. The following is for the nerd who wants to know how this is done. 

          
| Test | Interval | Method Name|
|------|----------|------------|
| Zone Changed | 15 seconds | 1-ZoneChanged |
| Poor GPS | 60 seconds | 2-PoorGPS |
| Interval Override | value | 3-Override |
| Old Location Data | 15 seconds | 4-OldLocationData |
| In a Zone | 1-hr or `inzone_interval` parameter | 5-InZone |
| Distance < 2.5km/1.5mi | 15 seconds | 6-Dist<2.5km/1.5mi |
| Distance < 3.5km/2mi | 30 seconds | 7-Dist<3.5km/2mi |
| Waze used and Waze time < 5 min. | time * `travel_time_factor` parmeter | 8-WazeTime |
| Distance < 5km/3mi | 1 minute | 9-Dist<5km/3mi |
| Distance < 8km/5mi | 3 minutes | 10-Dist<8km/5mi |
| Distance < 12km/7.5mi | 15 minutes | 11-Dist<12km/7.5mi |
| Distance < 20km/12mi | 10 minutes | 12-Dist<20km/12mi |
| Distance < 40km/25mi | 15 minutes | 13-Dist<40km/25mi |
| Distance < 150km/90mi | 1 hour | 14-Dist<150km/90mi |
| Distance > 150km/90mi | distance/1.5 | 15-Calculated |

*Notes:* The interval is then multiplied by a value based on other conditions. The conditions are:
1. If Stationary, keep track of the number of polls when you are stationary (the stationary count reported in the `info` attribute). Multiply the interval time by 2 when the stationary count is an even number and by 3 when it is divisible by 3.
2. If the direction of travel is Away, multiply the interval time by 2.
3. Is the battery is low, the GPS accuracy is poor or the location data is old, don't make any of the above adjustments to the interval.



