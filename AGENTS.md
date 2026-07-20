# AGENTS Guidelines for this Project

## Project Overview
BitCap IPReporter (bitcap-ipr) - a cross-platform IP reporter tool designed specifically for ASIC miners. It listens on a local network for miners via it's IP Report button and is able to retrieve additional miner data.

## Repository Structure
```
bitcap-ipr/
├── .github
│   └── workflows                        # Release/Test CI workflows
├── CLAUDE.md                            # Project guidance for Claude Code
├── CONFIGURATION.md                     # App configuration docs 
├── pyproject.toml                       # Project metadata
├── README.md                            # Main landing page 
├── resources                            # Static resources & app icons
│   ├── app
│   │   └── icons
├── scripts                              # scripts for packet generation/analysis
├── setup                                # App setup scripts (Inno setup)
├── src
│   ├── config.py                        # Configuration dataclass
│   ├── ipr.py                           # Main window class
│   ├── main.py                          # Entrypoint
│   ├── mod                              # Python modules
│   │   ├── ipr_asic                     # ASIC miner API library & client
│   │   │   ├── protocol                 # Base client & API protocol handlers
│   │   │   ├── client.py                # `ASICClient` Qt interface class
│   │   │   ├── data                     # Collection of data classes/parsers for miners
│   │   │   │   ├── miners               # Data parsers for miners
│   │   │   │   └── models.py            # Common data classes
│   │   │   ├── http                     # HTTP clients
│   │   │   ├── rpc                      # JSON-RPC clients; CGMiner
│   │   │   └── settings
│   │   │       └── __init__.py          # Global API settings
│   │   ├── lm                           # IP Report listening library & `ListenerManager` class
│   │   │   ├── iprd                     # Integration for IPR Daemon
│   │   │   │   └── listener.py          # `IPRDListener` listener class for IPRD 
│   │   │   ├── ipreport                 # `IPReport` dataclass & patterns
│   │   │   ├── listenermanager.py       # `ListenerManager` Qt interface class; Record
│   │   │   ├── listener.py              # `Listener` Qt UDP socket listener
│   │   └── updater                      # Self update checker/installer
│   ├── tests                            # Test suite/unittests
│   │   ├── payloads                     # Raw packet payloads for listener tests
│   ├── ui                               # Forms, widgets, and generated UI classes
│   │   ├── forms                        # Window .ui files
│   │   ├── ipr.qrc                      # Qt resource directory
│   │   ├── rc                           # Image assests
│   │   ├── theme.qss                    # Widget CSS/theming
│   │   └── widgets
│   │       ├── ipr                      # Core widgets
│   │       │   ├── idtable              # QTableView model/proxy
│   └── utils.py                         # Utility functions & metadata
```

## Key Modules
The core functionality of the IP reporter is resides in `src/mod`. These are the main modules within:
 - `lm` - IP Reporting (`ListenerManager` interface, UDP/TCP listening, packet patterns/validation)
 - `ipr_asic` - Asyncronous ASIC miner API library (`ASICClient` interface, HTTP/JSON-RPC/TCP clients, dataclasses)


## Tech Stack
 - Python 3.14.3 (pyenv)
 - PySide6 for Offical Qt Python bindings
 - Nuitka for build chain
 - pydantic for data models/classes
 - requests for facilitating HTTP method requests


 ## Environment
 Do not use system python3, always `.venv/bin/python` for running/testing this project.
 Run tests from `src/`, not the root directory.
 ```bash
cd src && ../.venv/bin/python -m unittest discover tests/
 ```
Included PySide6 tools:
  - `pyside6-uic` - use to generate Python classes from .ui forms
  - `pyside6-rcc` - use to generate resources from `ipr.qrc` file

## UI generation
There are included tools in the PySide6 suite that can automatically generate UI classes and app resources into Python code.

### UI class generation
```bash
cd src/ui/
pyside6-uic forms/mainwindow.ui -o MainWindow.py  # generate new MainWindow.py from mainwindow.ui file.
```

### Generating app resources
```bash
cd src/ui/
pyside6-rcc ipr.qrc -o resources.py  # generate app resources from ipr.qrc file.
```

## Testing
To test suite, run from `src/` directory:
```bash
cd src/ && ../.venv/bin/python -m unittest discover tests/
```

## Build & Run
bitcap-ipr is built using Nuitka to produce compiled binaries for multiple systems (Windows, MacOS, Linux).
There are some build scripts located in the root of repo to build local artifacts:
#### build_win.py script
```bash
./build_win.py -v <VERSION>              # build windows setup + portable version (.zip) with VERSION tag
./build_win.py -v <VERSION> --no-setup   # only build windows portable version.
```

#### build_linux.sh
```bash
./build_linux.sh -V <VERSION>    # build Linux (.deb) packge + portable version (.zip) with VERSION tag
./build_linux.sh -a              # only build Linux portable version.
```
Output artifacts are put in `dist/`

### Running
`src/main.py` can be ran locally with Python:
```bash
python3 src/main.py
```

## Releases
bitcap-ipr artifacts/releases are automatically built on git tags with workflows
