## Contributing

### Getting Started
To get started, set up the following enviroment

#### Requirements:
 - Python >= 3.10, <3.14
```bash
git clone https://github.com/bitcap-co/bitcap-ipr.git
cd bitcap-ipr
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r ./requirements.txt
# or with poetry
poetry install
# create symlink to resources within src
cd src
ln -s ../resources resources

# to run the app
python3 main.py
```

with any luck, the application should successfully launch!

### Debugging
The application has a logging system which is very useful for debugging. Within the enviroment, it is located at `./Logs/ipr.log`. You can also open the log within your default text editor within the app at "Help" -> "Open Log" in the menu.

To get debug level messages, you can change the log level within the app. Navigate to "Settings" -> "Settings" in the menubar, then change the log level within the "Logs" tab.

Or more simply you can change the `config.json` to:
```json
"logs": {
        "logLevel": "DEBUG",
        "maxLogSize": 1024,
        "onMaxLogSize": 0,
        "flushInterval": 0
    },
```
then launching the application.

#### Sending custom messages to the IP Reporter
To test listening, one can send their own message to the IP Reporter locally or over broadcast by using the `scripts/send_udp_dgram.py` script.

Example usage:
```bash
# sending bitmain/volcminer message
python3 scripts/send_udp_dgram.py -lp 14235 -m "<IP_ADDR>,AA:BB:CC:DD:EE:FF"
# sending iceriver message over broadcast
python3 scripts/send_udp_dgram.py -bp 11503 -m "addr:<IP_ADDR>"
```
