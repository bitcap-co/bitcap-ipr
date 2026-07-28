## ipr_asic (WIP)
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
 >- [ ] Miner errors
 - [x] Asyncronous clients to execute tasks in parellel (bulk actions)
 - [ ] Network scanning
 - Client support:
    * Backends
    >- [ ] cgminer/RPC API in parellel to retrieve runtime stats/status
    >- [ ] SSH client for GPU miners
    * Alternative authentacation
    >- [x] Try set alternative password first for authentication with API, falling back to hardcoded default password on fail

    * Miner control
    >- [x] Locate by blinking LEDs for set duration
    >- [x] Start/Stop, Restart, Reboot methods
    >- [ ] Update firmware

    * Miner configuration
    >- [x] Set/Update pool configuration
    >- [x] Set password authentication
    >- [ ] Network configuration
    >- [ ] Set Fan & Power modes
    >- [ ] Ability to set power/tune presets if supported (i.e. Vnish firmware)
    >- [ ] Reset configuration

 - Miner/Firmware support:
   - [x] Antminer (Stock) New Gen, 2020
   - [x] Iceriver (Stock)
   - [x] Whatsminer (Stock) V2,V3
   - [x] Goldshell (Stock)
   - [x] Sealminer (Stock)
   - [x] Volcminer (Stock)
   - [x] Elphapex (Stock)
   - [x] Auradine (Stock)
   - [ ] Hammer (Stock)
   - [ ] iPollo (Stock)
   - [x] Vnish firmware
   - [x] LuxOS firmware
   - [ ] HiveOS (GPU)
