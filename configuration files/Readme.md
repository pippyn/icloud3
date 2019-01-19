## Overview ##
The following describes the .yaml files that are used in my automations and scripts to support presence detection. The examples include leaving and arriving home, opening the garage door when arriving, entering and exiting zones, displaying details about the device, badges that show the location of a device, etc. Hopefully, this will serve as an example of how the iCloud3 platform can be used in it's entirety.  

The *Readme-LovelaceScreenshots.md* file shows example screen images.  

## Support Files ## 

**cov_garage_door.yaml** (Cover)  
A switch for the garage door is used on a Lovelace glance card to raise or lower the garage door. Covers and switches typically show the current state of the cover or switch. This one is setup to show an action (raise/lower) rather than the current state . It uses the custom_control_ui (https://github.com/andrey-git/home-assistant-custom-ui) to display the icon and text that describe the action and is set up in the customize.yaml file. The action is based on the current position of the door reported by *sensor.garage_door*.  

**device_tracker.yaml** (Device Trackers)  
Contains the configuration parameters for the iCloud3 device_tracker platform and sets up the mqtt platform to display a badge (*sensor.gary_badge* in *sn_badges.yaml*) on a Lovelace glance card. The badge shows the zone or distance Gary is from home.  

**ib_home_away_flags.yaml** (Input Boolean)  
Input boolean entities are used as flags to tell if a device is driving and far away from home; *input_boolean.gary_iphone_driving_flag* is set if more than 1-mile from home and *input_boolean.gary_iphone_far_away_flag* is set if more than 5-miles from home. The driving flag is used to open the garage door when Gary arrives home and was driving; the far_away flag is used to turn the hot water on and off.  

**is_icloud.yaml** (Input Select)  
The iCloud3 device tracker has numerous commands that are used to control it's operation. Examples are pausing and resuming polling, changing zones, changing the polling interval, changing the Waze operations, etc. This file contains command entries that can be used in Lovelace cards as an input_select.  

**sn_garage_door.yaml** (Sensor)  
The *sensor.garage_door* sensor defines the current state of the garage door (open or closed).  

**sn_badge.yaml** (Template Sensor)  
Badges are shown on a Lovelace glance card with information on Gary's location (*sensor.gary_badge*) and the position of the garage door (*sensor.garage_door_badge*).  

**sn_device_tracker_attributes.yaml** (Template Sensors)  
The *device_tracker.gary_iphone* entity contains many attributes showing the location, distance, zone, status, polling times and counts, etc. This template sensor creates separate entities for these attributes that can be used on Lovelace cards. They can also be used to trigger automations but should not be. Automations should be triggered by the device_tracker attributes themselves so the delay (in HA) updating the template sensor state will not delay the triggering of an automation.  

**sw_garage_door.yaml** (Switch)  
A switch is used to open and close the garage door. This file sets up the mqtt platform that contains the *switch.garage_door* entity. It can be tied to a smarthome z-wave device or a sonoff switch.

## Automations and Scripts ##  
The following automations and scripts control what happens when zone and distance events take place. A detailed description of each automation will help put the complete package together.  

**au_home_away_gary** (Automation)  
This contains automations that are triggered when Gary arrives home, leaves home, changes zones or is a specific distance from home. They are:

- *gary_arrives_home*  
>- Trigger - The *device_tracker.gary_iphone* state changes to home or the distance goes below .21 miles.  
>- Condition - The current state is 'not_home'. The condition is needed since the automation can be triggered by both events, one after the other and you do not want to run the automation more than once.  
>- Action - Run the *script.icloud_command_gary_iphone_zone_home* script to open the garage door if it is not already open and do other things related to arriving home (lights, security, etc.), issue a notification, change the *sensor.gary_badge* state to home and turn off the driving and far_away flags.

- *gary_leaves_zone*
>- Trigger - The *device_tracker.gary_iphone* state changes to not_home (Away).  
>- Condition - The current state is not 'not_home'. You do not want to run this automation again if the device is already not_home.  
>- Action - Run the *script.gary_leaves_home* script (which checks to see if the old zone is home), run the *script.icloud_command_gary_iphone_zone_not_home* script to catch leaving other zones and change the state of Gary's badge.  

- *gary_driving_flag_turn_on*, *gary_far_away_flag_turn_on*
>- Trigger - The *device_tracker.gary_iphone* distance is above certain values.  
>- Condition - The specific flags are off. 
>-  Action - Turn the specific flag on.

- *gary_driving_flag_turn_off* (Normally, this is turned off when gary arrives home, but sometimes, things don't happen when they should.)
>- Trigger - The *device_tracker.gary_iphone* state has been home for 15 minutes.
>- Condition - The driving flag is on. 
>- Action - Turn the driving flag off. 

**au_garage_door** (Automation)  
This contains automations that make sure the garage door is closed when no one is home or after 8pm. They are:

- *close_garage_door_after_8pm*  
>- Trigger - After 8pm.  
>- Condition - The garage door is open.  
>- Action - Close the garage door.

- *close_garage_door_no_one_home*  
>- Trigger - No one is home.  
>- Condition - The garage door is open.  
>- Action - Close the garage door.

**sc-icloud.yaml** (Script)  
This script file contains example scripts that issue service call commands to update the iCloud3 device tracker. The include general commands (reset, pause, resume, etc), set interval commands, zone commands (enter and exit) and commands for a specific device. 
