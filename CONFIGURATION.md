## IPR Configuration
BitCap IPReporter works right out of the box, but offers a lot of configuration/addiontional functionality to accomdate most of your needs!
This document gives an overview of main window user interface, additional configuration options, and extras.

### Top Menubar (Quick Options)
Along the top of the window, is the main interaction with the IP reporter in the form of a menu bar.

#### "Options" Menu
The "Options" menu contains settings relating to the core listener functionality.
Listener Behavior options:
   - "Always Open IP in Browser" Checkbox : When checked, the received IP address will automatically open in your default web browser.
   - "Disable Inactive Timer" : When checked, the listener will run until manually stopped instead of the default timeout of 15 minutes.
   - "Auto Start on Launch" : When checked, the listener will automatically start on application launch (Effective next launch on changed).

#### "ID Table" Menu
This menu contains settings relating to the ID Table view. When this view is enabled, the IP reporter will try to receive the following identifying information directly from it's API in their respective columns:
```
      SERIAL - miner serial number; Items in this column are editable on double click!
      SUBTYPE - miner model i.e "S19 XP"
      ALGORITHM - miner algorithm
      POOL - active pool URL
      WORKER active worker name
      FIRMWARE - installed firmware version
      PLATFORM - installed control board
```
"N/A" will be shown if that information is not available.
If the API client failed to authenticate or timeouts, "Failed" will be shown for all addtional columns.

   - "Enable ID Table" : When checked, updates the current view to the ID Table view.
   - "Open Selected IPs" : Once triggered, all selected IP addresses in the "IP" column will be opened in the default browser.
   - "Copy Selected Elements" : Once triggered, all selected elements in the table will be copied to the clipboard (seperated by comma).
   - "Import" : Once triggered, opens a file dialog to import a .csv file into the table view.
   - "Export" : Once triggered, the current data in the table will be exported to a .CSV file located in system's documents path.

### "Settings" Menu
Application settings:
   - "Settings..." : When triggered, updates the current view to the configuration view.

#### Application Settings ("Settings" Menu)
In the menubar, go to Settings -> "Settings..." to change the current view to the configuration view.
> [!NOTE]
> On MacOS, go to "Preferences..." (Command + ,)

Here is where you can change general, API, and log settings in their respective tabs.
   #### "General" tab
   - System Tray:
      - "Enable System Tray" : When checked, the system tray icon is created. From the icon, you can show/hide the main window, start/stop listening and quit the application. If the main window is hidden, you will get information messages and confirmations as system notifications.
      - "On Window Close" : When "Enable System Tray" is checked, you can change the window close behavior ("X" button clicked) to "Close" or "Minimize to tray" (default) to minimize the application to the system tray.
   - Inactive Timer:
     - "Use Custom Timeout" : When checked, enable ability to set custom inactive timer duration.
     - "Inactive Timeout: : When "Use Custom Timeout" is checked, you can change the duration using the spin box. Default is 15 minutues.
   - Listener Configuration:
      - Listener Configuration group box: When toggled, will set/unset all listeners within the listener configuration.
      - "Antminer" : When checked, enable listening for Antminers. Checked by default.
      - "Whatminer" : When checked, enable listening for Whatsminers. Checked by default.
      - "IceRiver" : When checked, enable listening for IceRivers. Checked by default.
      - Additional Miners (disabled by default):
         - "Goldshell" : When checked, enable listening for Goldshell miners.
         - "Volcminer" :  When checked, enable listening for VolcMiners.
         - "Sealminer" : When checked, enable listening for Sealminers.
         - "Elphapex" : When checked, enable listening for Elphapex miners.
         - "Dragonball" : When checked, enable listening for Dragonball miners.

   #### "API" tab
   "Settings" group:
    - Locate Duration : Configure the blink duration when locating a miner. Default is 10s.

  "Authentication" group:
   If you have an alternative password other then the default, you can set it here for the respective miner type/firmware to be able use with the ID Table view:
   - Bitmain/Antminer:
     - "Set Login Password" : Set alternative login password for Antminers. If blank, "root" is used for authentication.
   - Whatsminer:
     - "Set Login Password" : Set alternative login password for Whatsminers. If blank, "admin" is used for authentication.
   - Volcminer:
     - "Set Login Password": Set alternative login password for Volcminers. If blank, "ltc@dog" is used for authentication.
   - Goldshell
     - "Set Login Password": Set alternative login for Goldshell miners. If blank, "123456789" is used for authentication.
   - Bitdeer/Sealminer:
     - "Set Login Password": Set alternative login for Sealminers. if blank, "seal" is used for authentication.
   - Vnish:
     - "Set Login Password": Set alternative login for Vnish firmware. if blank, "admin" is used for authentication.
     - "Use Antminer Login" Checkbox : When checked, it will set the alternative login for Vnish to be the same as the supplied Antminer login.
   - pbfarmer:
     - "Set API Key" : Set alternative API Key to access IceRivers using pbfarmer firmware. If blank, the default API key is used for authentication.

   #### "Logs" tab
   - Log settings:
     - "Log Level" : Set the desired base log level for the logger. The log file will only record that level and greater. Below are the available levels:
     ```
     DEBUG - log debug messages; lowest level
     INFO - log info messages; default level
     WARNING - log warning messages
     ERROR - log error messages
     CRITICAL - log critical/exception messages
     ```
     - "Max Log Size" : Set the maximum file size for the log file in KB. Default is 1024kb and max limit is 4096kb.
     - "On Max Log Size" : Set the behavior for when the log file reaches the max log size value. "Flush" will flush/empty the current log to be used again. "Rotate" will rotate to a new log file, adding a number suffix to the old log file. Default is "Flush"
     - "Flush Interval" : Set to override the flush interval. If set to "Close", the current log file will be flushed/emptied on application close. Default is "On Max Log Size".

### Default Configuration File
```json
{
    "general": {
      "enableSysTray": false,
      "onWindowClose": 0,
      "useCustomTimeout": false,
      "inactiveTimeoutMins": 15,
      "listenFor": {
        "antminer": true,
        "whatsminer": true,
        "iceriver": true,
        "additional": {
          "volcminer": false,
          "goldshell": false,
          "sealminer": false,
          "elphapex": false,
          "dragonball": false
        }
      }
    },
    "api": {
      "auth": {
        "bitmainAltPasswd": "",
        "whatsminerAltPasswd": "",
        "volcminerAltPasswd": "",
        "goldshellAltPasswd": "",
        "bitdeerAltPasswd": "",
        "firmware": {
          "vnishAltPasswd": "",
          "pbfarmerKey": ""
        }
      },
      "settings": {
        "locateDurationSecs": 10,
        "vnishUseAntminerLogin": false
      }
    },
    "logs": {
      "logLevel": "INFO",
      "maxLogSize": 1024,
      "onMaxLogSize": 0,
      "flushInterval": 0
    },
    "instance": {
      "geometry": {
        "mainWindow": []
      },
      "options": {
        "alwaysOpenIPInBrowser": false,
        "disableInactiveTimer": false,
        "autoStartOnLaunch": false
      },
      "table": {
        "enableIDTable": false
      }
    }
}
```
