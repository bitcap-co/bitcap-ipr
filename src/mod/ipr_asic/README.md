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
 - [x] Simplistic Qt-compatiable interface to identify/use various backends 
 * [ ] Standarized `MinerData` model to retrieve identifing information & current status/stats
 >- [ ] Standardized Model
 >- [ ] CGminer/RPC API runtime status/stats
 - [x] Asyncronous clients to execute tasks in parellel (bulk actions)
 - Client support:
    * Backends
    >- [ ] cgminer/RPC API in parellel to retrieve runtime stats/status
    * Alternative authentacation
    >- [x] Try set alternative password first for authentication with API, falling back to hardcoded default password on fail

    * Miner control
    >- [x] Locate by blinking LEDs for set duration
    >- [ ] Start/Stop, Restart, Reboot methods
    >- [ ] Update firmware

    * Miner configuration
    >- [x] Set/Update pool configuration
    >- [ ] Set password authentication
    >- [ ] Set Fan & Power modes
    >- [ ] Ability to set power/tune presets if supported (i.e. Vnish firmware)
 - Miner/Firmware support:
   - [x] Antminer (Stock) New Gen, 2020
   - [x] Iceriver (Stock)
   - [x] Whatsminer (Stock) V2,V3
   - [x] Goldshell (Stock)
   - [x] Sealminer (Stock)
   - [x] Volcminer (Stock)
   - [x] Elphapex (Stock)
   - [x] Auradine (Stock)
   - [x] Vnish firmware
   - [x] LuxOS firmware
   - ...
