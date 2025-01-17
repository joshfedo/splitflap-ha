# splitflap-ha
A HA integration for https://github.com/scottbez1/splitflap

This is in early alpha and bugs should be expected. PRs are encouraged. 
## Requirements
MQTT installed and configured in Home Assistant
MQTT enabled and configured on your split flap display

## Features
* Allows for a simple configuration in HA
* Ability to center short text 
* Support pagination for long messages
  * Messages longer then your display will be split into multiple pages
* Overflow handling for displays with rows
  * hyphenate or push long words to new lines
* Blank out the display after a message is shown.
![img.png](img.png)

## Setup
1. Install the integration via HACS
2. Devices > + Add Integration
   1. search for splitflap
3. Enter the MQTT topic (Default "splitflap")
4. Enter the number of modules in your display
5. Enter the number of rows in your display. 
6. In the new splitflap integration click configure on your device to set your options.

## Usage
1. Enter a message in on the device to publish to the display
   1. The integration will automatically capitalize your input. 
2. For v2 displays with colors, you can show a color by adding a "\" before the color code. 
   1. ie for white "\w", "\whello\w"

##install
The simplest way to install this integration is with the Home Assistant Community Store (HACS). 

Setting up a custom repository is done by:

Go into HACS from the side bar.
Click into Integrations.
Click the 3-dot menu in the top right and select Custom repositories
In the UI that opens, copy and paste the url for this github repo into the Add custom repository URL field.
Set the category to Integration.
Click the Add button. Further configuration is done within the Integrations configuration in Home Assistant. You may need to restart home assistant and clear your browser cache before it appears, try ctrl+shift+r if you don't see it in the configuration list.

