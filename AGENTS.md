# AGENTS Guidelines for bitcap-ipr

## Project Overview
BitCap IPReporter (bitcap-ipr) - a cross-platform IP reporter tool designed specifically for ASIC miners. It listens on a local network for miners via it's IP Report button and is able to retrieve additional miner data.

## Key Modules
The core functionality of the IP reporter is resides in `src/mod`. These are the main modules within:
 - `lm` - IP Reporting (`ListenerManager` interface, `Listener` class for local UDP port listening, `ipreport` submodule for packet patterns/validation)
 - `lm/iprd` - IPR Daemon backend integration (IPRDListener, IPRDServiceListener for IPRD service discovery)
 - `powermonitor` - Cross-platform power/suspend monitoring to respect system power state for IPR listening
 - `ipr_asic` - Asyncronous ASIC miner API library (`ASICClient` interface, HTTP/JSON-RPC/TCP clients, dataclasses)

 ## Other modules
 - `mod/updater` - Automatic updates for the IP reporter (Downloads/installs updates from GitHub releases)
 - `src/ui/` - widgets, .ui files, resources/assets, generated UI classes, widget theming (QSS)
 - `src/ui/ipr` - Core IPR UI widgets
 - `src/ui/ipr/idtable` - QTableView model/proxy componnts for IPR data display

## Tech Stack
 - Python 3.14.3 (pyenv)
 - PySide6 for Offical Qt Python bindings
 - Nuitka for build chain
 - pydantic for data models/classes
 - httpx for facilitating async HTTP method requests


 ## Environment Guide
 - Do not use system python3, always `.venv/bin/python` for running/testing this project.
 - Run tests from `src/`, not the root directory.
 ```bash
cd src && ../.venv/bin/python -m unittest discover tests/
 ```
 - Use pydantic models for dataclasses/model validation/serialization

## UI generation
There are included tools in the PySide6 suite that can automatically generate UI classes and app resources into Python code.

 - Generate UI classes from .ui forms using `pyside6-uic`
 ```bash
cd src/ui/ && pyside6-uic forms/mainwindow.ui -o MainWindow.py  # generate new MainWindow.py from mainwindow.ui file.
```
 - Generate app resources from `ipr.qrc` file using `pyside6-rcc`
```bash
cd src/ui/ && pyside6-rcc ipr.qrc -o resources.py  # generate app resources/assets from ipr.qrc file.
```

## Test suite
To test suite, run from `src/` directory:
```bash
cd src/ && ../.venv/bin/python -m unittest discover tests/
```

## Build & Run
bitcap-ipr is built using Nuitka to produce compiled binaries for multiple systems (Windows, MacOS, Linux).
```bash
.venv/bin/python -m nuitka src/main.py --assume-yes-for-downloads --standalone --output-file=BitCapIPR --output-dir=dist/BitCapIPR

.venv/bin/python -m nuitka src/main.py --assume-yes-for-downloads --msvc=latest --windows-console-mode=disable --standalone --output-file=BitCapIPR --output-dir=dist/BitCapIPR # windows (msvc)
```
Output artifacts are put in `dist/`

### Running
`src/main.py` can be ran locally with Python:
```bash
.venv/bin/python src/main.py
```

## Releases
bitcap-ipr artifacts/releases are automatically built on git tags with workflows
