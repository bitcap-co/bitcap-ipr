## BitCap IPReporter
A cross-platfrom IP Reporter tool for Antminer, Whatsminer, and IceRiver ASICs.

![BitCapIPR main window](/.github/imgs/ipr.png)


## Included Features
 - Listen for Antminers, IceRivers, and Whatsminers concurrently!
 - Copy confirmation IP & MAC address to clipboard.
 - Open confirmation IP in web browser.
 - Custom "ID Table" view (ID Table -> "Enable ID Table").
    - Retrieve identifying information like Serial, Type, Subtype/Model, Algo, Firmware, Platform.
    - Export table to .CSV file (ID Table -> "Export").
    - API support for stock and custom firmwares (Vnish, pbfarmer).
    - Locate miners by blinking.
 - System Tray support.
 - Logs (Help -> "Open Log").

## Requirements
A workstation/PC directly connected to main network or VLAN.

> [!NOTE]
> For WhatsMiners on DHCP, need to be plugged in to same VLAN/network as miner.

## Installation
BitCapIPR is supported on Debian Linux (AMD64), Windows (X64), and MacOS (X64/ARM).

Download the latest installer for your OS and Arch from [Releases](https://github.com/bitcap-co/bitcap-ipr/releases).

Portable artifacts are also available!

## Building application from source (Pyinstaller)
clone the source repo.

depends: python3.11+
OPTIONAL: python3-venv
```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r ./requirements.txt
pyinstaller src/ipr.spec --noconfirm
# move the readme into dist to create local files
cp ./README.md ./dist/BitCapIPR
```

## Usage
To start using BitCap IPR, simply press the "Start" button!
The app will automatically start listening for Antminers, Whatsminers, and IceRivers.

Once the listeners have started, press the "IP Report" button on the desired miner.
After, a confirmation window should show detailing the IP & MAC address.

> [!NOTE]
> By default, the listeners will only run for 15 minutes and automatically stop. To change, go to Options -> "Disable Inactive Timer".
> The listeners will automatically restart on change to apply.

## API Setup for IDing/Locating
The ID Table uses the respected API Client for the detected miner to retreive identifing data or locating.

You can supply alternative API authentication for Antminers/Whatsminers/pbfarmer in the API settings tab in the configuration view. The IP reporter will try these passwords first, then the default authentication. If these settings are left blank, only the default authentication is used.

>[!NOTE]
> See [Configuration](./CONFIGURATION.md) to learn more about configuring the IP reporter.
