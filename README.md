## BitCap IPReporter
A cross-platfrom IP Reporter tool for Bitmain, Whatsminer, and IceRiver ASICs.

## Requirements
A workstation/PC directly connected to main network or vlan.

> [!NOTE]
> For WhatsMiners on DHCP, need to be plugged in to same vlan/network as miner.

## Installation
BitCapIPR is supported on Debian Linux (AMD64), Windows (X64), and MacOS (X64/ARM).

Download the latest installer for your OS and Arch from [Releases](https://github.com/bitcap-co/bitcap-ipr/releases).

Portable artifacts are also available!

## Building application from source (Pyinstaller)
clone the source repo

depends: python3.11+
OPTIONAL: python3-venv
```bash
python3 -m venv .venv
source .venv/bin/activate
pip3 install -r ./requirements.txt
pyinstaller src/ipr.spec --noconfirm
```

## Included Features
 - Listen for Antminers, IceRivers, and Whatsminers concurrently!
 - Copy confirmation IP & MAC address to clipboard.
 - Open confirmation IP in web browser. (Or can always open in browser: Options -> 'Always Open IP in browser')
 - Custom table view to get more data from miners like serial number, type and subtype. (Table -> 'Enable ID Table')
 - Supply custom password for table data retrieval. (Settings -> 'Set API Password')
 - Drag-select elements from table view to copy for easy sending or export table data to .CSV.
 - System Tray support. (Settings -> 'Enable System Tray')
