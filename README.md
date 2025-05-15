## BitCap IPReporter

## A cross-platfrom IP Reporter tool for Antminer, Whatsminer, and IceRiver ASICs.

![BitCap IPReporter running on Windows](/.github/imgs/ipr.png)

*BitCap IPReporter running on Windows*


## Included Features
 - Listen for Antminers, IceRivers, and Whatsminers concurrently!
   - With additional support for Goldshell, VolcMiner, and Sealminers.
 - Copy confirmation IP & MAC addresses to clipboard.
 - Open confirmation IP addresses in web browser.
 - Custom "ID Table" view for retrieving identifying information from miners (i.e. SN, type, subtype/model, algorithm, firmware, and platform).
   - API support including some custom firmwares (Vnish, Pbfarmer).
   - Locate miners by blinking.
   - Export table to .CSV file
 - System Tray support.


## Requirements
A workstation/PC directly connected to main network or VLAN.

> [!NOTE]
> For WhatsMiners on DHCP, need to be plugged in to same VLAN/network as miner.


## Installation
BitCapIPR is supported on Debian-flavored Linux (x64), Windows (x64), and MacOS (x64/ARM).

Download the latest installer for your OS and Arch from [Releases](https://github.com/bitcap-co/bitcap-ipr/releases).

Portable artifacts are also available!

> [!NOTE]
> macOS binaries are not signed. Due to this, the IP Reporter will probably fail to launch and get an error stating the the app is from an unknown source.
> To Fix: Manully allow through System Settings -> `Security and Privacy`.
>
> If macOS complains that the app is damaged, run the following command:
> ```
> sudo xattr -dr com.apple.quarantine /path/to/BitCapIPR.app
> ```
> Now the app should be able to run normally.


## Usage
To start listening with BitCap IPR, simply press the "Start" button!
The app will automatically start listening for Antminers, Whatsminers, and IceRivers.

Press the "IP Report" button on the miner and a IP confirmation window should show detailing the IP & MAC address.

> [!NOTE]
> By default, the listeners will only run for 15 minutes and automatically stop. To disable this, go to the top menubar and select Options -> "Disable Inactive Timer".


## Further Configuration
BitCap IPR supports various configuration settings to customize the behavior to your liking. See [Configuration](./CONFIGURATION.md) for more information on all the available settings.


### API Setup
When using the ID Table, IPR will create an API session for the received miner IP and gather miner data.

By default, it will use the default authentication. If you have an alternative password set, you can supply it to the IP Reporter by going to the API tab in Settings -> "Settings..." from the menubar.
> [!NOTE]
> On MacOS, go to "Preferences..." (Command + ,)


## Building application from source (Pyinstaller)
clone or download the source repo.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r ./requirements.txt
pip install pyinstaller
pyinstaller src/ipr.spec
# move the readme into dist to create files and run locally
cp ./README.md ./dist/BitCapIPR
```


## Troubleshooting/Reporting Issues
If encountering an issue with the IP reporter, take the following steps:
1. Go to Help -> "Open Log" to get insight on the issue.
2. If not able to resolve from log, can report an issue on the repo by going to Help -> "Report Issue". Please include log file or snippet in the issue.
