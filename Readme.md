# iCloud3 (doc. v1.3)
[\](https://github.com/gcobb321/icloud3/blob/master/README.md)]

----------

iCloud3 is an improved version of the iCloud device_tracker component installed with Home Assistant.  
  
It is installed as a custom device_tracker component in the config/custom_component/device_tracker directory. Instructions are found at the end of this document. 

## INTRODUCTION

**How it works**

iCloud3 polls the device on a dynamic schedule based on:
 - The device in a zone or not in a zone.
 - The distance from 'home' to your current location. Two methods are used to determine the distance:
    1. A calculation giving the 'line-of-sight' distance based on the GPS coordinates of both locations.
    2. From [Waze](http://www.waze.com), the map/driving/direction service, to get the driving distance based on the most direct route. 
 - The travel time to 'home' if the Waze service is being used. 
 - The direction you are going — towards home, away from home or stationary.
 - The battery level.
 - The accuracy of the GPS location or if the last poll returned a location that the iCloud service determined was 'old'.

The above analysis results in a polling interval. The further away from home and the longer the travel time back to home, the longer the interval; the closer to home, the shorter the interval. The polling interval checks each device being tracked every 15 seconds to see if it's location should be updated. If so, it and all of the other devices being tracked with iCloud3 are updated (more about this below). With a 15 second interval, you track the distance down 1/10 of a mile/kilometer. This gives a much more accurate distance number that can used to trigger automations. You no longer limited to entering or exiting a zone. 

Note: The `pyicloud.py` Python component is part of Home Assistant and used to poll the device, requesting location and other information. If the iCloud account is associated with multiple devices, all of the devices are polled, whether or not the device is being tracked by Home Assistant. This is a limitation of pyicloud.py. 


**What other programs do I need**

The `Home Assistant IOS App` is all. You do not need `OwnTracks` or other location based trackers and you do not need `nmap`, `netgear`, `ping` or any network monitor. The `Home Assistant IOS App` will notify Home Assistant when you leave home and iCloud3 device tracker will start keeping up with the device's location, the distance to home and the time it will take to get there.  
   
*Note:* The IOS App settings `Zone enter/exit`, `Background fetch` and `Significant location change` location settings need to be enabled. 


The `iCloud` platform allows you to detect presence using the  [iCloud](https://www.icloud.com/) service. iCloud allows users to track their location on iOS devices. Your device needs to be registered with “Find My iPhone”.
  
  
**Home Assistant Configuration**

To integrate iCloud in Home Assistant, add the following section to your `configuration.yaml` file:

```
# Example configuration.yaml entry
device_tracker:
  - platform: icloud3
    username: USERNAME 
    password: PASSWORD
    account_name: accountname
    include_devive_type: iphone

```

**About Your Apple iCloud Account**
  
Apple has enabled '2 Step Authentication' for iCloud accounts. To permit Home Assistant, and iCloud3, to access your iCloud account,  you need to have an authentication code sent via a text message to a trusted device, which is then entered in Home Assistant. The duration of this authentication is determined by Apple, but is now at 2 months.  
  
*Note:* `pyicloud`, the Python program used to access your iCloud account, does not support 2 Factor Authentication, the improved version of 2 Steps Authentication.

When your account needs to be authorized, or reauthorized, you will be notified and the Notification symbol (the bell in the upper right of the Home Assistant screen) will be highlighted. Take the following steps to complete the process:  
  1. Press the Notification Bell.
  2. A window is displayed, listing the trusted devices associated with your account. It will list an number (0, 1, 2, etc.) next to the phone number that can receive the text message containing the 2 Step Authentication code number used to authenticate the computer running Home Assistant (your Raspberry Pi for example).
  3. Type the number.
  4. A text message is sent. Type the authentication code you receive in the next window that is displayed.
  
*Note:* When you use iCloud account is accessed on a new device, you may receive an email from Apple stating that someone has logged into your account.  

## CONFIGURATION VARIABLES

**username**  
*(Required)* The username (email address) for the iCloud account. 

**password**  
*(Required)* The password for the account.

**account_name**  
The friendly name for the account_name.  
*Note:*If this isn’t specified, the account_name part of the username (the part before the `@` in the email address) will be used.

**include_device_types**  (or  **include_device_type**)  
**exclude_device_types**  (or  **exclude_device_type**)  
Include or exclude device type(s) that should* be tracked.  
*Default: Include all device types associated with the account*  

```
# Example yaml
include_device_type: iphone
```
```
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
  - lillianiphone
```
*Note:* It is recommended that to you specify the devices or the device types you want to track to avoid confusion or errors. All of the devices you are tracking are shown in the `devices_tracked ` attribute.  

**inzone_interval**  
The interval between location upates when the device is in a zone. This can be in seconds, minutes or hours, e.g., 30 secs, 1 hr, 45 min, or 30 (minutes are assumed if no time qualifier is specified).  
*Default: 1 hr*

**gps_accuracy_threshold**  
iCloud location updates come with some gps_accuracy varying from 10 to 5000 meters. This setting defines the accuracy threshold in meters for a location updates. This allows more precise location monitoring and fewer false positive zone changes. If the gps_accuracy is above this threshold, a location update will be retried again in 2 minutes to see if the accuracy has improved. After 5 retries, the normal interval that is based on the distance from home, the waze travel time and the direction will be used.  
*Default: 1000*

*Note:* The accuracy and retry count are displayed in the `info` attribute field (*GPS.Accuracy-263(2)*) and on the `poll_count`  attribute field (*2-GPS*). In this example, the accuracy has been poor for 2 polling cycles.  

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
 
## ATTRIBUTES

There are numerous attributes that are available for use in automations or to monitor the location of your device. They are shown in following table.  

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
  
**battery**  
The battery level.  
  
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
  
### Accessing Attributes in Automations and in Lovelace

Automations can access the attribute's value using the `states.attributes.attributename` statement. The third trigger in the example below will trigger the `gary_arrives_home` automation when the distance goes below .25.  

```
# Example yaml (automation.yaml)
- alias: gary_arrives_home
  trigger:
 
    - platform: state
      entity_id: device_tracker.garyiphone
      to: 'home'
 
    - platform: state
      entity_id: device_tracker.garyiphone
      to: 'near_home'
 
    - platform: numeric_state
      entity_id: device_tracker.garyiphone
      value_template: '{{float(state.attributes.distance)}}'
      below: .25

```  
  
An entity's state can be displayed on a Lovelace card but the attribute's value cannot. To display the attribute's value, a sensor template can be used that will be updated when the attribute's value changes. The following example will display the `distance` attribute.  
  
```
# Example yaml (sensor.yaml)
- platform: template
  sensors:
    garyiphone_distance:
      value_template: '{{float(state_attr("device_tracker.garyiphone","distance"))}}'
      unit_of_measurement: 'mi'

```

And on a Lovelace card:
```
# Example yaml
- entity: sensor.garyiphone_distance
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
| icloud_lost_phone | Play the Lost Phone sound  |
| icloud_reset | Reset the iCloud3 custom component  |

Description of each service follows.
  
#### SERVICE — icloud_update
This service allows you to change the way iCloud3 operates. The following parameters are used:

| Parameter | Description |
|-----------|-------------|
| account_name | account_name of the iCloud3 custom component specified in the Configuration Variables section described at the beginning of this document. |
| device_name | Name of the device to be updated. All devices will be updated if this parameter is not specified. |
| command | The action to be performed (see below)|
| parameter | Additional parameters for the command |
  
The following commands are available:. 
  
| Command |  Parameter | Description |
|---------|------------|-------------|
| pause |  | Stop updating/locating a device (or all devices). You
| resume |  | Start updating/locating a device (or all devices) again |  
| resume |  | Reset the update interval if it was overridden the 'set_interval' service |
| pause-resume |  | Toggle pause and resume commands |
| zone | zonename | Change iCloud3 state to 'zonename' (like the device_tracker.see service call) and immediately update the device interval and location data. Note: Using the device_tracker.see service call will be delayed until the next 15-second update iteration rather than immediately. |
| waze | on | Turn on Waze. Use the 'waze' method to determine the update interval |
| waze | off | Turn off Waze. Use the 'calc' method to determine the update interval |
| waze | toggle | Toggle waze on or off |
|  waze | reset_range | Reset the Waze range to the default distances (min=1, max=99999) |
| debug | interval | Show how the update interval is determined |
  

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
        device_name: garyiphone
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
        device_name: garyiphone
        command: zone home
        
icloud_command_garyiphone_zone_not_home:
  alias: 'Gary - Zone not_home'
  sequence:
    - service: device_tracker.icloud_update
      data:
        account_name: gary_icloud
        device_name: garyiphone
        command: zone not_home
```

  
#### SERVICE — icloud_set_interval  
This service allows you to override the interval between location updates to a fixed time. It is reset when a zone is entered or when the icloud_update service call is processed with the 'resume'command. The following parameters are used:

| Parameter | Description |
|-----------|-------------|
| account_name | account_name of the iCloud3 custom component specified in the Configuration Variables section described at the beginning of this document. |
| device_name | Name of the device to be updated. All devices will be updated if this parameter is not specified. |
| interval | The interval between location updates. This can be in seconds, minutes or hours. Examples are 30 sec, 45 min, 1 hr,  hrs, 30 (minutes are assumed if no time descriptor is specified). |

```
#Example Automations.yaml           
icloud_set_interval_15_sec_gary:
  alias: 'Set Gary to 15 sec'
  sequence:
    - service: device_tracker.icloud_set_interval
      data:
        account_name: gary_icloud
        device_name: garyiphone
        interval: '15 sec'
 
icloud_set_interval_1_min_gary:
  alias: 'Set Gary to 1 min'
  sequence:
    - service: device_tracker.icloud_set_interval
      data:
        account_name: gary_icloud
        device_name: garyiphone
        interval: 1

icloud_set_interval_5_hrs_all:
  alias: 'Set interval to 5 hrs (all devices)'
  sequence:
    - service: device_tracker.icloud_set_interval
      data:
        account_name: gary_icloud
        interval: '5 hrs'
 
```
  
#### SERVICE — icloud_lost_iphone 
This service will play the Lost iPhone sound on a certain iDevice. 

| Parameter | Description |
|-----------|-------------|
| account_name | account_name of the iCloud3 custom component specified in the Configuration Variables section described at the beginning of this document. |
| device_name | Name of the device to be updated. All devices will be updated if this parameter is not specified. |
  
#### SERVICE — icloud_reset
This service will reset an iCloud3 device data in the same manner when Home Assistant is started. This is helpful when not all devices are being found by the iCloud3 component or if you have added a new iDevice to your account.
  
| Parameter | Description |
|-----------|-------------|
| account_name | account_name of the iCloud3 custom component specified in the Configuration Variables section described at the beginning of this document. |



  
