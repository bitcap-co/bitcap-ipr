## BitCap IPReporter

## A cross-platform IP Reporter tool for Antminer, Whatsminer, and IceRiver ASICs.

![BitCap IPReporter running on Windows](/.github/imgs/ipr.png)

*BitCap IPReporter running on Windows*


## What's Included
 - Listen for IP Report messages from Antminers, Icerivers, Whatsminers all concurrently.
   - With additional support for:
      - Hammer
      - Volcminer
      - Sealminer
      - Elphapex
      - Goldshell
      - and more on the way!
 - Fully dynamic listening
    - Select what miners to listen for at any time!
    - Listen filtering to ONLY allow specified miners.
 - System Tray support!
 - Miner API support including some custom firmwares (Vnish, LuxOS).
 - Use "alternative" (non-default) passwords for miner authentication.
 - Custom "ID Table" view for retrieving identifying information from received miners.
    - Table view for displaying more identifying data like miner type, model, serial number, firmware, pool info, etc.
    - Import/Export table as .CSV.
    - Locate miners by blinking.
 - Retrieve and update pool configuration with the Pool Configurator!
 - Load/Save pool information with presets.


## Requirements
A workstation/PC connected to miner network (LAN/VLAN).

> [!NOTE]
> For WhatsMiners on DHCP, need to be plugged in to same VLAN/network as miner.


## Installation
The BitCap IPReporter (later referred to as IPR) is supported on Debian-flavored Linux (x64), Windows 10/11 (x64), and MacOS (x64/ARM).

Download the latest installer for your OS and Arch from [Releases](https://github.com/bitcap-co/bitcap-ipr/releases).

Portable artifacts are also available!

## Usage
To start listening with IPR, simply press the "Start" button!
The app will automatically start listening for all supported miners by default. This can be freely adjusted as needed in the "Listener Configuration" section in Settings.

Press the "IP Report" button on the miner and a IP confirmation window should show detailing the IP & MAC addresses.


### API Setup
When using the ID Table, IPR will create an API session for the received miner IP and automatically gather miner data.

By default, it will use the default authentication. If you have an alternative password set, you can supply it to the IP Reporter by going to the API tab in Settings -> "Settings..." from the menubar.
> [!NOTE]
> On MacOS, go to "Preferences..." (Command + ,)


## Further Configuration
IPR supports various configuration settings to customize the behavior to your liking. See [Configuration](./CONFIGURATION.md) for more information on all the available settings.


## Known Issues & Workarounds
 - ### MacOS binary is damaged/unknown source
> macOS binaries are not signed. Due to this, the IP Reporter will probably fail to launch and get an error stating the the app is from an unknown source.
> To Fix: Manully allow through System Settings -> `Security and Privacy`.
>
> If macOS complains that the app is damaged, run the following command to remove the entry from the anti-virus:
> ```bash
> sudo xattr -dr com.apple.quarantine /path/to/BitCapIPR.app
> ```
> Now the app should be able to run normally.

## Troubleshooting/Reporting Issues
If encountering an issue with the IP reporter, take the following steps:
  1. Go to Help -> "Open Log" to get insight on the issue.
  2. If not able to resolve from log, can report an issue on the repo by going to Help -> "Report Issue". Please include log file or snippet in the issue.


## License
This project is licensed under the GNU General Public License v3.0 -- see [LICENSE.txt](./LICENSE.txt)
  

## Trademarks
The names "bitcap-ipr", "BitCap IPReporter", "Bit Capital Group", "BitCap", and associated logos are not covered by the project license; see [TRADEMARKS.md](./TRADEMARKS.md) or contact sales@bitcap.co for permission.
