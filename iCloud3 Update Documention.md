### iCloud3 Updates:

##### Version .86 - 1/22/2019

1. Fixed a problem where devices were being excluded when they shouldn't have been. For example: if you had an *include_device: gary* and an *exclude_device: garyold* in the configuration file, gary was not being included in the devices being handled by iCloud3 when it should have been.
2. Added better support for more than one iCloud3 platform for different Apple iCloud accounts. The attributes now show the correct devices being tracked and the accounts they are associated with.
3. Updated the documentation to better explain naming devices on the device (iPhone, iPad, etc.) and in the HA IOS app. Also better explained what happens if you do not use the IOS app on the device.