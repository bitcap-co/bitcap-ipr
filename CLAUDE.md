# CLAUDE.md

## Project Overview
bitcap-ipr is a cross-platform standalone ASIC miner IP Reporter tool built with the Qt framework. Its able to fetch miner data from various supported ASIC miner types initiated from IP report
messages/datagrams from the local network.

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

## Testing
To test listeners, run from `src/` directory:
```bash
cd src/
python3 -m unittest discover tests/
```

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

## Structure
 - `resources/` -  App icons/static files
 - `scripts/` - helper scripts to produce/analyze specific datagrams/packets
 - `setup/` - setup utilites
 - `src/mod/` - local python modules
 - `src/tests/` - unit tests
 - `src/ui/` - forms, widgets and generated UI code.

## Key components
 - `src/mod/lm` - ListenerManager module: faciliates IP report listening
 - `src/mod/apiv2` - ASIC miner API library
 - `src/ui/widgets` - custom Qt widgets

## Tech stack
 - Python 3.14.3
 - PySide6 6.11.1
 - Nuitka for build toolchain
 - Pydantic for dataclasses
