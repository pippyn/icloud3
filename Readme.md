# iCloud3 (doc. v1.3)
[\](https://github.com/gcobb321/icloud3/blob/master/README.md)]

----------

iCloud3 is an improved version of the iCloud device_tracker component installed with Home Assistant.  
  
It is installed as a custom device_tracker component in the config/custom_component/device_tracker directory. Instructions are found at the end of this document. 


**How it works**

iCloud3 polls the device on a dynamic schedule based on:
 - The device in a zone or not in a zone.
 - The distance from 'home' to your current location. Two methods are used to determine the distance:
    - A calculation giving the 'line-of-sight' distance based on the GPS coordinates of both locations.
    - From [Waze](http://www.waze.com), the map/driving/direction service, to get the driving distance based on the most direct route. 
 - The travel time to 'home' if the Waze service is being used. 
 - The direction you are going — towards home, away from home or stationary.
 - The battery level.
 - The accuracy of the GPS location or if the last poll returned a location that the iCloud service determined was 'old'.

The above analysis results in a polling interval. The further away from home and the longer the travel time back to home, the longer the interval; the closer to home, the shorter the interval. The polling interval checks each device being tracked every 15 seconds to see if it's location should be updated. If so, it and all of the other devices being tracked with iCloud3 are updated (more about this below). With a 15 second interval, you track the distance down 1/10 of a mile/kilometer. This gives a much more accurate distance number that can used to trigger automations. You no longer limited to entering or exiting a zone. 

Note: The `pyicloud.py` Python component is part of Home Assistant and used to poll the device, requesting location and other information. If the iCloud account is associated with multiple devices, all of the devices are polled, whether or not the device is being tracked by Home Assistant. This is a limitation of pyicloud.py. 


**What other programs do I need**

The Home Assistant IOS app is all. You do not need `OwnTracks` or other location based trackers and you do not need  `nmap`, `netgear`, `ping` or any network monitor. The `IOS` app will notify Home Assistant when you leave home and iCloud3 will start keeping up with the device's location, the distance to home and the time it will take to get there.  
   
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


### CONFIGURATION VARIABLES

**username**  
*(Required)* The username (email address) for the iCloud account. 

**password**  
*(Required)* The password for the username. 

**account_name**  
The friendly name for the account_name. If this isn’t given, it will use the account_name of the username (the part before the `@` in the email address).

**include_device_types**  (or  **include_device_type**)  
**exclude_device_types**  (or  **exclude_device_type**)  
Include or exclude device type(s) that should be tracked.  
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
 
### ATTRIBUTES

There are numerous attributes that are available for use in automations or to monitor the location of your device. They are shown in following table.  

**interval**  
The current interval between update requests to your iCloud account for the location and other information. They increase as you get further away and decrease as you get closer to home.  
  
**travel_time**  
The Waze travel time to return home from your current location.  
  
**distance**  
The distance from home being used by the interval calculator. This will be either the Waze distance or the calculated distance.  
  
**waze_distance**  
The distance from home returned by Waze.  
  
**calculated_distance**  
The calculated distance.  
  
**dir_of_travel**  
The direction you are traveling — towards home, away from home, near home, or stationary. This is calculated based on the distance from home on this location update and the last one. Stationary can be a little difficult to determine at times and sometimes needs several updates to get right.  
  
**last_located**  
The last time your iCloud account successfully located the device. Normally, this will be a few seconds after the update time, however, if you are in a dead zone or the GPS accuracy exceeds the threshold, the time will be older. In this case, a description of the issues is displayed in the `info` attribute field.  
  
**last update**  
The time of the last iCloud location update.  
  
**next_update**  
The time of three next iCloud location update.  
  
**poll_count**
The number of iCloud location updates done that day.  
  
**info**  
A message area that displays information about the device. This includes the battery level, Waze status, GPS accuracy issues, how long the device has been stationary, etc.  
  
**battery**  
The battery level.  
  
**tracked_devices**
The devices that are being tracked based on the 'includes' and 'excludes' specified in the configuration.yaml file.  This will be the same for all devices tracked.  
  
**device_status**  
The status of the device — online if the device is located and offline if polling has been paused or it can not be located.  
  
**battery_status**
Charging or NotCharging.  
  
**latitude, longitude, altitude**
The location of the device.  
  
**source_type**  
How the device was located to include gps, beacon, router.  
  

  







### ABOUT YOUR ICLOUD ACCOUNT

You may receive an email from Apple stating that someone has logged into your account.

To disable the drainage of the battery, a dynamic interval is being used for each individual device instead of a fixed interval for all devices linked to one account. The dynamic interval is based on the current zone of a device, the distance towards home and the battery level of the device.

2 Steps Authentication is enabled for iCloud. The component will ask which device you want to use as Trusted Device and then you can enter the code that has been sent to that device. The duration of this authentication is determined by Apple, but is now at 2 months, so you will only need to verify your account each two months, even after restarting Home Assistant. 2 Factor Authentication is the improved version of 2 Steps Authentication, this is still not supported by the pyicloud library. Therefore it’s not possible to use it with the device_tracker yet.

4 services are available for this component:

-   **icloud_update**: This service can be used to ask for an update of a certain iDevice. The  `account_name`  and  `device_name`  are optional. Request will result in new Home Assistant  [state_changed](https://www.home-assistant.io/docs/configuration/events/#event-state_changed)  event describing current iphone location. Can be used in automations when manual location update is needed, e.g., to check if anyone is home when door’s been opened.
-   **icloud_lost_iphone**: This service will play the Lost iPhone sound on a certain iDevice. The  `account_name`  and  `device_name`  are optional.
-   **icloud_set_interval**: This service will change the dynamic interval of an iDevice. The  `account_name`  and  `device_name`  are optional. If  `interval`  is used in the service_data, the iDevice will be updated with that new interval. That interval will be fixed until the iDevice changes zone or if this service is called again. If  `interval`isn’t used in the service_data, the interval for that iDevice will revert back to its default dynamic interval based on its current zone, its distance towards home and its battery level.
-   **icloud_reset_account**: This service can be used to reset an iCloud account. This is helpful when not all devices are being found by the component or if you have added a new iDevice to your account. The  `account_name`  is optional.


<!--stackedit_data:
eyJoaXN0b3J5IjpbMTU1MjQwMDUwMl19
-->
