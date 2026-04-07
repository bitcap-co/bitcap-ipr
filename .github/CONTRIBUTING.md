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
# make sure dev dependencies are installed in your venv
poetry install --with dev
# verify nuitka version
python3 -m nuitka --version
```
Within the root of the repo, there are some build scripts for Linux and Windows. Execute from project root.
#### Building Linux Binaries
```bash
# building for Linux example, will build .deb package and portable version (archive)
./build_linux.sh -V 1.0.0
# to just build portable/archive, add --archive-only
./build_linux.sh -V 1.0.0 --archive-only
```
#### Building Window Binaries
```powershell
# building for Windows example, will build setup.exe and portable version (archive)
py.exe build_win.py -v 0.0.0
# to just build portable/archive, add --no-setup
py.exe build_win.py -v 0.0.0 --no-setup
```

Artifacts will be put in the generated `dist` folder after completion.

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
cd src && python3 -m unittest discover tests/
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
