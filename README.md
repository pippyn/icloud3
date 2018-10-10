# icloud3

# iCloud3
[\](https://github.com/gcobb321/icloud3/blob/master/README.md)]

----------

The  `icloud`  platform allows you to detect presence using the  [iCloud](https://www.icloud.com/)  service. iCloud allows users to track their location on iOS devices.

It does require that your device is registered with “Find My iPhone”.

To integrate iCloud in Home Assistant, add the following section to your  `configuration.yaml`  file:

```
# Example configuration.yaml entry
device_tracker:
  - platform: icloud
    username: USERNAME
    password: PASSWORD
    account_name: accountname

```

### [](https://www.home-assistant.io/components/device_tracker.icloud/#configuration-variables)CONFIGURATION VARIABLES

[](https://www.home-assistant.io/components/device_tracker.icloud/#username)username

(string)(Required)The username for the iCloud account.

[](https://www.home-assistant.io/components/device_tracker.icloud/#password)password

(string)(Required)The password for your given username.

[](https://www.home-assistant.io/components/device_tracker.icloud/#account_name)account_name

(string)(Optional)The friendly name for the account_name. If this isn’t given, it will use the account_name of the username (so the part before the  `@`  in the email address).

[](https://www.home-assistant.io/components/device_tracker.icloud/#max_interval)max_interval

(integer)(Optional)Maximum interval in minutes between subsequent location upates. This tracker uses dynamic intervals for requesting location updates. When iphone is stationary, interval will eventually be set to  `max_interval`  to save battery. When iphone starts moving again interval will be dynamically updated to 1 min. Note that updating interval to 1 min might be delayed by maximum  `max_interval`  minutes. Minimum value is 1 min.

Default value: 30

[](https://www.home-assistant.io/components/device_tracker.icloud/#gps_accuracy_threshold)gps_accuracy_threshold

(integer)(Optional)iCloud location updates come with some gps_accuracy varying from 10 to 5000 meters. This setting defines the accuracy threshold in meters for a location update. Less accurate updates will be discarded by this tracker. This allows more precise location monitoring and fewer false positive zone changes.

Default value: 1000

Low  `max_interval`  may cause battery drainage as it wakes up your device to get the current location.

You may receive an email from Apple stating that someone has logged into your account.

To disable the drainage of the battery, a dynamic interval is being used for each individual device instead of a fixed interval for all devices linked to one account. The dynamic interval is based on the current zone of a device, the distance towards home and the battery level of the device.

2 Steps Authentication is enabled for iCloud. The component will ask which device you want to use as Trusted Device and then you can enter the code that has been sent to that device. The duration of this authentication is determined by Apple, but is now at 2 months, so you will only need to verify your account each two months, even after restarting Home Assistant. 2 Factor Authentication is the improved version of 2 Steps Authentication, this is still not supported by the pyicloud library. Therefore it’s not possible to use it with the device_tracker yet.

4 services are available for this component:

-   **icloud_update**: This service can be used to ask for an update of a certain iDevice. The  `account_name`  and  `device_name`  are optional. Request will result in new Home Assistant  [state_changed](https://www.home-assistant.io/docs/configuration/events/#event-state_changed)  event describing current iphone location. Can be used in automations when manual location update is needed, e.g., to check if anyone is home when door’s been opened.
-   **icloud_lost_iphone**: This service will play the Lost iPhone sound on a certain iDevice. The  `account_name`  and  `device_name`  are optional.
-   **icloud_set_interval**: This service will change the dynamic interval of an iDevice. The  `account_name`  and  `device_name`  are optional. If  `interval`  is used in the service_data, the iDevice will be updated with that new interval. That interval will be fixed until the iDevice changes zone or if this service is called again. If  `interval`isn’t used in the service_data, the interval for that iDevice will revert back to its default dynamic interval based on its current zone, its distance towards home and its battery level.
-   **icloud_reset_account**: This service can be used to reset an iCloud account. This is helpful when not all devices are being found by the component or if you have added a new iDevice to your account. The  `account_name`  is optional.


