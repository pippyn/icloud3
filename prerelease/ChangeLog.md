### iCloud3 Prerelease Change Log:



##### Known Issues:

1. Possible problems when issuing commands for a specific device with more than one icloud account.
2. Errors updating a device when the location information is old. An error message is written to the log file and the device is repolled constantly retried without successfully relocating the device. 

##### Version 0.86.2 - 1/27/2019

1. The iCloud3 zone state was capitalized', i.e., *school* went to *School*, *HOMEZONE* went to *Homezone*. The zone's friendly_name  is now used without any reformatting. If there is no *zone.friendly_name* attribute, the state will be capitalized.
2. If the location data was 'old', an "Error updating device_name" message was displayed in the log file due to inconsistent data. Additional error checking has been added.
3. Devices in a zone were repolled via Find-my-Friends if another device on the account needed to be repolled. If the device in a zone (that didn't need to be repolled) was experiencing poor GPS accuracy, that lead to device location errors and it would potentially drop in-and-out of the zone until the GPS accuracy was restored and may get into a relocate loop for several cycles. Now, the device in the zone will only be updated if there were no GPS accuracy issues.

##### Version 0.86.1 - 1/25/2019

1. Fixed a problem where an error returning location data from the iCloud Find-my-Friends location request would crash iCloud3 and put it into an endless retry loop.
2. Changed the way log records (information, error, debug) are written to the HA log file. Also added a new *info logging* command that starts (and stops) writing debug records to the HA log file to make troubleshooting easier.
3. Changed the coordinates of the Dynamic Stationary Zone from 0°, 0° (Papa New Guinea) to 0°,180° (where the international date line crosses the equator).
4. Add Version information to the iCloud3.py file to support the Custom Control Updater program.
5. Added a Prerelease directory to the Github Repository for early versions of iCloud3.

##### Version 0.86 - 1/22/2019

1. Fixed a problem where devices were being excluded when they shouldn't have been. For example: if you had an *include_device: gary* and an *exclude_device: garyold* in the configuration file, gary was not being included in the devices being handled by iCloud3 when it should have been.
2. Added better support for more than one iCloud3 platform for different Apple iCloud accounts. The attributes now show the correct devices being tracked and the accounts they are associated with.
3. Updated the documentation to better explain naming devices on the device (iPhone, iPad, etc.) and in the HA IOS app. Also better explained what happens if you do not use the IOS app on the device.