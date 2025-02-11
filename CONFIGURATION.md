## Configuration
IPR offers a lot of confirguration out of the box.

### Menubar Options
Options - This menu contains listener settings:
   - "Always Open IP in Browser" : When this option is checked, the receieved IP address will automatically open in your default browser and no IP Confirmation will be shown.
   - "Disable Inactive Timer" : When this option is checked, The listener will run until manually stopped instead of the default timeout of 15 minutes.
   - "Auto Start on Launch" : when this option is checked, the listener will automatically start on application launch. (Effective on next launch after change)

ID Table - This menu contains settings relating to the ID Table:
   - "Enable ID Table" : When this option is checked, it will update the current view to a table view. The IP reporter will now retrieve and store the following identifing miner data directly from it's API:
   ```
      IP - IP address of miner
      MAC - MAC address of miner
      SERIAL - miner serial number if available
      TYPE - miner type (antminer, iceriver, whatsminer, etc)
      SUBTYPE - miner model
      ALGORITHM - miner algorithm if available
      FIRMWARE - installed firmware version
      PLATFORM - installed control board if available
   ```
   - "Open Selected IPs" : once triggered, it will open the selected items in the IP column in a new tab in your default browser.
   - "Copy Selected Elements" : once triggered, it will open all the selected elements in the table to your clipboard.
   - "Export" : once triggered, it will export the current table as an .CSV file to your Documents path.

### Application Settings
In the menubar, go to Settings -> "Settings..." to change the current view to the configuration view. Here is where you can change General, API, and log settings in their respective tabs.
   #### "General" tab
   - System Tray settings:
      - "Enable System Tray" : When checked, the system tray icon is created. From the icon, you can Show/Hide the main window, start/stop listening and quit the application. If the main window is hidden, you will get system notifications for information messages and new confirmations.
      - "On Window Close" : When "Enable System Tray" is checked, you can change the window close behavior ("X" button clicked) to quit the application or minimize to the system tray.
   #### "API" tab
   Here you can supply alternative API authentication for Antminers/Whatsminers/pbfarmer. the IP reporter will try these passwords first, then using the default authentication. If these settings are left blank, only the default authentication is used.
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
     - "On Max Log Size" : Set the behavior for when the log file reaches the max log size value. "Flush" will flush/empty the current log. "Rotate" will rotate to a new log file, adding a number suffix to the old log file. Default is set to flush/empty the current log.
     - "Flush Interval" : Set the desired flush interval. If set to "Close", the current log file will be flushed/emptied on application close. Default is on max log size.


### Default configuration
```json
{
    "general": {
        "enableSysTray": false,
        "onWindowClose": 0
    },
    "api": {
        "bitmainAltPasswd": "",
        "whatsminerAltPasswd": "",
        "pbfarmerKey": ""
    },
    "logs": {
        "logLevel": "INFO",
        "maxLogSize": "1024",
        "onMaxLogSize": 0,
        "flushInterval": 0
    },
    "instance": {
        "options": {
            "alwaysOpenIPInBrowser": false,
            "disableInactiveTimer": false,
            "autoStartOnLaunch": false
        },
        "table": {
            "enableIDTable": true
        }
    }
}
```