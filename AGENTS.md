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
- Do not use system `python3`; always use `.venv/bin/python` or `poetry run python` for this project.
- Poetry is the dependency manager. Treat `pyproject.toml` and `poetry.lock` as authoritative; do not add or manually maintain a `requirements.txt` file.
- Install locked runtime and development dependencies with:
  ```bash
  make install
  # Equivalent: poetry install --with dev --no-interaction
  ```
- Run tests through `make test`, which verifies generated metadata and runs the suite from `src/`.
- Use pydantic models for dataclasses/model validation/serialization.

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
Run the complete test suite from the repository root:
```bash
make test
```

The equivalent direct command, which must run from `src/`, is:
```bash
cd src/ && ../.venv/bin/python -m unittest discover tests/
```

## Application Metadata
- `pyproject.toml` is the source of truth for the application version, description, URLs, and static application/company metadata.
- `src/app_metadata.py` is generated from `pyproject.toml`; do not edit it by hand.
- After changing metadata or the version, regenerate and validate it:
  ```bash
  make metadata
  make metadata-check
  ```
- Tagged builds validate that the Git tag, such as `v1.6.0`, matches the project version.

## Build & Run
BitCap IPReporter uses Nuitka to produce binaries for Windows, macOS, and Linux. The shared build entry point is `tools/build_app.py`; do not duplicate Nuitka or packaging commands in workflows or platform scripts.

```bash
# Build a portable archive for the current platform.
make build

# Build the portable archive and platform package/installer.
make package

# Cross-platform direct equivalents when make is unavailable.
poetry run python tools/build_app.py --portable-only
poetry run python tools/build_app.py
```

Nuitka's invariant project options remain in `src/main.py`. Variable metadata, output paths, and packaging behavior belong in `tools/build_app.py`, `tools/build_support.py`, or the modules under `tools/builders/`.

Output artifacts and `nuitka-report.xml` are written to `dist/`.

### Running
Run the application locally with:
```bash
make run
# Equivalent: .venv/bin/python src/main.py
```

## Releases
- `.github/workflows/build.yml` builds release artifacts with Python 3.14 on Git tags matching `v*`.
- The release workflow also supports manual runs through `workflow_dispatch`.
- CI must install dependencies from `poetry.lock` and call `tools/build_app.py`, keeping local and CI builds aligned.
- Release tags must match the version in `pyproject.toml`; generate `src/app_metadata.py` before tagging.
