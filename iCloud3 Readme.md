# icloud3

# iCloud3
[\](https://github.com/gcobb321/icloud3/blob/master/README.md)]

----------

ICloud3 is a much improved location tracker than the original iCloud tracker installed with Home Assistant. It is installed as a custom device_tracker component in the config/custom_component/device_tracker directory. Instructions are found at the end of this document. 

**How it works**

iCloud3 polls the device on a dynamic schedule based on:
. If the device in a zone.
. The distance from 'home' to your current location. Two methods are used to determine the distance – (1) a calculation giving the 'line-of-sight' distance based on the GPS coordinates of both locations and (2) from Waze, the map/driving/direction service, to get the driving distance based on the most direct route. 
. The travel time to 'home' if the Waze service is being used. 
. If you are going towards home, away from home or stationary. 
. The battery level.
. The accuracy of the GPS location or if the last poll returned a location that the iCloud service determined was 'old'.

The above analysis results in a polling interval. The further away from home and the longer the travel time, the longer the interval; the closer to home, the shorter the interval. The polling interval checks each device being tracked every 15 seconds to see if it's location should be updated. If so, it and all of the other devices being tracked are updated (more about this below). 




The  `pyicloud.py`  Python component is part of Home Assistant and used to poll the device, requesting location and other information. If the iCloud account is associated with multiple devices, all of the devices are polled, whether or not the device is being tracked by Home Assistant. This is a limitation of pyicloud.py. 


---------
The  `icloud`  platform allows you to detect presence using the  [iCloud](https://www.icloud.com/)  service. iCloud allows users to track their location on iOS devices.

It does require that your device is registered with “Find My iPhone”.

To integrate iCloud in Home Assistant, add the following section to your  `configuration.yaml`  file:

```
# Example configuration.yaml entry
device_tracker:
  - platform: icloud3
    username: USERNAME 
    password: PASSWORD
    account_name: accountname

```




### CONFIGURATION VARIABLES

**username**

(string)(Required) The username (email address) for the iCloud account. 

**password**

(string)(Required) The password for the username. 

**account_name**

(string)(Optional) The friendly name for the account_name. If this isn’t given, it will use the account_name of the username (so the part before the  `@`  in the email address)

**inzone_interval**

(Optional) The interval between location upates when the device is in a zone. This can be in minutes or hours, e.g., 1 hr, 45 min, or 30. Minutes are assumed if no time qualifier is specified. 

Default: 1 hr.

 This tracker uses dynamic intervals for requesting location updates. When iphone is stationary, interval will eventually be set to  `max_interval`  to save battery. When iphone starts moving again interval will be dynamically updated to 1 min. Note that updating interval to 1 min might be delayed by maximum  `max_interval`  minutes. Minimum value is 1 

**gps_accuracy_threshold**

(integer)(Optional) iCloud location updates come with some gps_accuracy varying from 10 to 5000 meters. This setting defines the accuracy threshold in meters for a location updates. This allows more precise location monitoring and fewer false positive zone changes. If the gps_accuracy is above this threshold, a location update will be retried in 2 minutes (up to 5 times) to see if the accuracy has improved. At that time, the normal interval based on distance from home, waze travel time and direction will be used.

Note: The accuracy and retry count are displayed in the  `info`  attribute (ex. GPS.Accuracy-263(2)) and on the  `poll_count`  attribute (2-GPS)

Default value: 1000



 

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
eyJoaXN0b3J5IjpbMzIxODU5OTMwLC0zMTc3MTU3NzcsODA2OT
E5MjUzXX0=
-->