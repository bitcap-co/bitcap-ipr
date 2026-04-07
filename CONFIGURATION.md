## IPR Configuration
BitCap IPReporter works right out of the box, but offers a lot of configuration/addiontional functionality to accomdate most of your needs!

Below is the default configuration file. All of these options can be found in the UI of the application. The comments provide an brief overview of what each configuration does and generally where they correlate in the UI.

### Default Configuration File
```json
{
  // "General" settings
  "general": {
    "enableSystemTray": false, // Enable/Disable system tray icon.
    "onWindowClose": 0, // window on close behavior (X). 0 = "Minimize to Tray", 1 = "Close".
    "useCustomTimeout": false, // Enable/Disable custom inactive timeout duration.
    "inactiveTimeoutDuration": 15 // the duration of the inactive timeout in minutes.
  },
  // "Listener Configuration" settings
  "listener": {
    "enableFiltering": false, // Enable/Disable listener filtering.
    "enableAll": true, // Enable/Disable all listeners. 
    // Enable/Disable listening for specific miners.
    "listenFor": {
      "antminer": true,
      "whatsminer": true,
      "iceriver": true,
      "hammer": true,
      "volcminer": true,
      "goldshell": true,
      "sealminer": true,
      "elphapex": true
    }
  },
  // "API" Settings
  "api": {
    "locateDuration": 10, // locate/blink duration in seconds.
    // Set alternative passwords (non-default) for specific miner types/firmware
    "auth": {
      "antminerAltPasswd": "",
      "iceriverAltPasswd": "",
      "whatsminerAltPasswd": "",
      "goldshellAltPasswd": "",
      "hammerAltPasswd": "",
      "volcminerAltPasswd": "",
      "elphapexAltPasswd": "",
      "sealminerAltPasswd": ""
    },
    // set Alternative passwords for firmwares
    "firmware": {
      "useAntminerLogin": false, // Use same alternative password set in Antminer Login.
      "vnishAltPasswd": ""
    }
  },
  // Pool Configurator store
  "poolConfigurator": {
    "autoSetWorkers": true,  // Enable/Disable auto append worker names derivied from serial/mac to user. (.XXXXX)
    "selectedPoolPreset": -1,
    // Stored pool presets
    "poolPresets": []
  },
  // "Log" Settings
  "logs": {
    "logLevel": "INFO", // Change logger level. accepted values: "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL"
    "flushOnClose": false, // Enable/Disable flush log file on application close.
    "maxLogSize": 1024, // Set max log size in KB. Max value 4098kb or 4MB.
    "onMaxLogSize": 0 // Log behavior once log file reaches maxLogSize. 0 = "Flush", 1 = "Rotate" 
  },
  // "Instance" settings (Top menu bar)
  "instance": {
    "geometry": [],
    // "Options" menu
    "options": {
      "alwaysOpenIP": false, // Enable/Disable always open received IP address in default browser.
      "disableInactiveTimer": false, // Enable/Disable the inactive listening timer.
      "autoStartOnLaunch": false, // Enable/Disable auto start listeners on application launch.
      "clearTableOnStop": false, // Enable/Disable clear ID Table data when listening is stopped.
      "confirmsStayOnTop": false // Enable/Disable IP Confirmations stay on top of desktop.
    },
    "views": {
      "showIDTable": false, // Enable/Disable the ID Table view.
      "showPoolConfigurator": false // Enable/Disable the Pool Configurator view.
    }
  }
}
```
