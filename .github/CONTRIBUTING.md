## Contributing

### Getting Started
To get up and running with BitCapIPR, it requires the following enviroment:

#### Minimum Requirements:
 - Python >= 3.10, <3.15

### Project Environment Setup
Below are instructions for Linux, but can be easily converted for whatever OS/enviroment you are running on.

```bash
# Clone project
git clone https://github.com/bitcap-co/bitcap-ipr.git
cd bitcap-ipr
# Create virtual enviroment
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
# install dependencies with poetry (recommended)
poetry install
# to install with dev dependencies (for local building/testing)
poetry install --with dev

# to run BitCapIPR locally, create symlink from within src to ../resources
cd src
ln -s ../resources resources

# launch BitCapIPR
python3 main.py
```

with any luck, the application should successfully launch!

### Building Binaries
Binaries are made with Nuitka.
Make sure you have the one of the supported compilers for your OS [here](https://nuitka.net/user-documentation/user-manual.html#requirements)

If you are using Linux, make sure you have the following system depenedencies:
 - `binutils`
 - `patchelf`
 - `ccache` (Optional; used to speed up re-compilication)
Which can be installed with your package manager.
```bash
# Install the locked runtime and development dependencies.
poetry install --with dev
# Verify the Nuitka version selected by poetry.lock.
poetry run python -m nuitka --version
```

Builds on every platform use the same Python entry point. The package version and
application metadata come from `pyproject.toml`.

```bash
# Build the portable archive for the current platform.
make build

# Build the portable archive and the platform package/installer.
make package

# Cross-platform commands when make is unavailable (for example, Windows).
poetry run python tools/build_app.py --portable-only
poetry run python tools/build_app.py
```

Linux packaging requires `dpkg-deb` and `zip`. macOS installer builds require
`create-dmg`, and Windows installer builds require Inno Setup 6. Artifacts and a
Nuitka compilation report are written to `dist/`.

The old `build_linux.sh` and `build_win.py` commands remain as compatibility
wrappers around `tools/build_app.py`.

#### Updating release metadata

Edit the version and other static application metadata in `pyproject.toml`, then
regenerate and verify the runtime constants:

```bash
make metadata
make metadata-check
```

A tagged build fails if the tag does not match the project version. For example,
`v1.6.0` requires `version = "1.6.0"` in `pyproject.toml`. Release builds can also
be started manually from the GitHub Actions workflow.

### Debugging
The application has a logging system which is very useful for debugging. Within the enviroment, it is located at `./Logs/ipr.log`. You can also open the log within your default text editor within the app at "Help" -> "Open Log" in the menu.

To get debug level messages, you can change the log level within the app. Navigate to "Settings" -> "Settings" in the menubar, then change the log level within the "Logs" tab.

Or more simply you can change the `config.json` to:
```json
"logs": {
  "logLevel": "DEBUG",
  "flushOnClose": false,
  "maxLogSize": 1024,
  "onMaxLogSize": 0
},
```
then launching the application.

### Running tests
For now, there is only one test that verifies that the lm module is working properly. Ensuring that datagram parsing and validation is working for all supported IP Report formats.

To verify, can simply run:
```bash
make test

# Equivalent direct command:
cd src && ../.venv/bin/python -m unittest discover tests/
```

#### Simulating IP Report messages
For specific scenarios, one might want to test specific IP report messages. Within `scripts` there are some handy scripts to help with this.

For most cases, `send_dgram.py` should surrfice. You can send custom datagrams locally or over broadcast (255.255.255.255).

```bash
# send dgram message to port 14235 locally
python3 scripts/send_dgram.py -p 14235 "<MESSAGE>"

# send dgram message to port 14235 over broadcast
python3 scripts/send_dgram.py -bp 14235 "<MESSAGE>"
```
See ```python3 scripts/send_dgram.py -h``` for more details.
