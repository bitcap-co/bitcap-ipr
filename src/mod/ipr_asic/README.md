## ipr_asic
`ipr_asic` aims to be a simplistic ASIC/GPU miner API library for interacting with various miners. Developed along-side with bitcap-ipr!

#### Key Features
  - Standarized asyncronous API with simplifed interface
  - Miner identication
  - Standarized miner data
  - Miner control (Locate, Start/Stop, Restart, Reboot, Update)
  - Miner configuration (password authentication, Pools, Fans, Tune/Presets)
  - Support for alternative authentication
  - Network scanning
  - Support for HiveOS/GPU miners

#### Goals
 - Simplistic Qt-compatiable interface to identify/use various backends 
 - Standarized `MinerData` model to retrieve identifing information & current status/stats
 - Asyncronous clients to execute tasks in parellel (bulk actions)
 - Client support:
    >- Alternative authentacation
    Try set alternative password first for authentication with API, falling back to hardcoded default password on fail
    >- Miner control
    - Locate by blinking LEDs for set duration
    - Start/Stop, Restart, Reboot methods
    - Update firmware
    >- Miner configuration
    - Set/Update pool configuration
    - Set password authentication
    - Set Fan & Power modes
    - Ability to set power/tune presets if supported (i.e. Vnish firmware)
 - Miner/Firmware support:
   - Antminer (Stock)
   - Iceriver (Stock)
   - Whatsminer (Stock) V2 & V3 API
   - Goldshell (Stock)
   - Sealminer (Stock)
   - Volcminer (Stock)
   - Elphapex (Stock)
   - Auradine (Stock)
   - Vnish firmware
   - LuxOS firmware
   - ...
