## Configuration

### Menubar Options
Options - This menu contains listener settings:
   - "Always Open IP in Browser" : When this option is checked, the receieved IP address will automatically open in your default browser and no IP Confirmation will be shown.
   - "Disable Inactive Timer" : When this option is checked, The listener will run until manually stopped instead of the default timeout of 15 minutes.
   - "Auto Start on Launch" : When this option is checked, the listener will automatically start on application launch (Effective next launch on changed).

ID Table - This menu contains settings relating to the ID Table:
   - "Enable ID Table" : When this option is checked, it will update the current view to a table view. The IP reporter will now retrieve and store the following identifying miner data directly from it's API:
   ```
      SERIAL - miner serial number if available
      SUBTYPE - miner model
      ALGORITHM - miner algorithm if available
      FIRMWARE - installed firmware version
      PLATFORM - installed control board if available
   ```
   - "Open Selected IPs" : Once triggered, all selected IP addresses in the "IP" column will be opened in the default browser.
   - "Copy Selected Elements" : Once triggered, all selected elements in the table will be copied to the clipboard (seperated by comma).
   - "Export" : Once triggered, the current data in the table will be exported to a .CSV file located in system's documents path.

### Application Settings
In the menubar, go to Settings -> "Settings..." to change the current view to the configuration view. Here is where you can change General, API, and log settings in their respective tabs.
   #### "General" tab
   - System Tray:
      - "Enable System Tray" : When checked, the system tray icon is created. From the icon, you can show/hide the main window, start/stop listening and quit the application. If the main window is hidden, you will get information messages and confirmations as system notifications.
      - "On Window Close" : When "Enable System Tray" is checked, you can change the window close behavior ("X" button clicked) to "Close" (default) or "Minimize to tray" to minimize the application to the system tray.
   #### "API" tab
   - Bitmain/Antminer:
     - "Set Login Password" : Set alternative login password for Antminers. If blank, "root" is used for default authentication.
   - Whatsminer:
     - "Set Login Password" : Set alternative login password for Whatsminers. If blank, "admin" is used for default authentication.
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
