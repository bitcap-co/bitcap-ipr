## ListenerManager (lm) module
the `lm` module contains the IP Report listening API for bitcap-ipr. Through the main `ListenerManager` class, its able to manage a multitude of listeners for the various miner types that bitcap-ipr supports.

## Structure
`ipreport` - submodule that validates/parses various IP Report messages from miners.

`listener.py` - A custom QObject centered around QUDPSocket that sends validated IPReport data back to `ListenerManager` via signals.

`listenermanager.py` - A custom QObject class that manages one or more configured listeners and broadcasts the received IPReport data via signals. Used as the default/"out-of-box" on-device IP report listening backend for the IP Reporter.

## Overview

### The ListenerManager class

The `ListenerManager` class handles a list of individual listeners specific for each miner type and captures IPReport data. Below defines the basic IPReport dataclass structure:
```python
class IPReport(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    created_at: float = Field(default_factory=time.time)
    updated_at: float = 0
    hint: MinerTypeHint = MinerTypeHint.UNKNOWN
    miner_hint: str = ""
    sort_ip: int = -1
    ip: str = ""
    mac: str = ""
    serial: str = ""
```
A few key items in this structure are the `ip` (source IP address of miner), `mac` (source MAC address of miner) and `hint` (type of miner determined by the destination UDP port).

For the most part, each miner type has an unique port that they send their IP Report message to.
```python
class MinerTypeHint(IntEnum):
    UNKNOWN = 0
    COMMON = 14235
    ICERIVER = 11503
    WHATSMINER = 8888
    SEALMINER = 18650
    GOLDSHELL = 1314
    ELPHAPEX = 9999
    AURADINE = 12345
    IPOLLO = 54321
    HIVEGPU = 42069
    IBELINK = 6667
```
As we can see, for example, IceRiver sends to `11503`, Whatsminer send to `8888`, etc. Port `14235` is marked as common because we could get a couple different miner types (Antminer, Hammer, Volcminer). But for the most part, we can see what type of miner is it just based off of the port number! For "COMMON" types, further identification can be used via it's API.

### Listener configuration
We can give a configuration to the ListenerManager to create the necessary UDP listeners needed to listen for multiple miner types. We use a QButtonGroup made directly from the Listener Configuration options in the app.

```python
self.listenerConfig = QButtonGroup(self, exclusive=False)
self.listenerConfig.addButton(self.checkListenAntminer, 1)
self.listenerConfig.addButton(self.checkListenIceRiver, 2)
self.listenerConfig.addButton(self.checkListenWhatsminer, 3)
self.listenerConfig.addButton(self.checkListenVolcminer, 4)
self.listenerConfig.addButton(self.checkListenHammer, 5)
self.listenerConfig.addButton(self.checkListenGoldshell, 6)
self.listenerConfig.addButton(self.checkListenSealminer, 7)
self.listenerConfig.addButton(self.checkListenElphapex, 8)
self.listenerConfig.addButton(self.checkListenAuradine, 9)
self.listenerConfig.addButton(self.checkListenIPollo, 10)
self.listenerConfig.addButton(self.checkListenIBeLink, 11)
```

Based off the the button ID and whether or not it is enabled, we can determine which listeners to start. Also ensuring that we only have one socket for each port (In the case of listening for Antminer and Volcminer, for example).

### Processing Datagrams
When we receive a new message/datagram on the network, we verify the message to ensure it is what we are expecting. We do these by pattern matching the message to make sure we have what we expect given the miner type. Then we try and parse the message into our IPReport structure.

Once it is deemed as valid and have parsed our message, we send our result back to the ListenerManager. If is not a valid message (i.e we failed to match or parse), we ignore the message and listen for the next.

## Duplicate packets
Some miners may send the same packet multiple times within a short window.

To solve this, the ListenerManager holds a Record which is an fixed-size ordered dictionary to see what we have sent previously and uses it to check if we should send again. Each record entry is indexed by the source IP address of the packet with the associated IPReport data.

```python
def is_duplicate(self, value: IPReport) -> bool:
    """Returns True if the given IPReport is a duplicate of an existing entry.
    Existing entries can be re-emitted if they are older than RECORD_MIN_AGE.
    """
    previous = self.get(value.ip)
    if previous is None:
        return False
    if previous.mac != value.mac:  # MAC mismatch; update existing entry
        return False
    if time.time() - previous.updated_at <= RECORD_MIN_AGE:
        logger.warning(f" [{value.ip}] : duplicate packet.")
        return True
    return False
```

Once we received an result from a listener, we will run the above method to check all previous record entries and see if we have "seen" this IP address before. if we have, we compare further with the MAC address to ensure this is came from the same miner. If that also passes, we compare the record minimum age. Each record has a minimum age of 10 seconds before it can be sent again. So if its has been 10 seconds or shorter, we mark as duplicate packet and ignore. Otherwise we will send the new IPReport.


## Signals
The ListenerManager communicates with the IPR window class using Qt Signals & Slots. Once we have a IP Report that we can send we emit the listen_complete signal with our IPReport data. If we encounter some sort of listener error, it will emit the error_received signal with the ListenerError attached. Bind errors (port is already in use) are treated as a seperate error that we emit with bind_failed.

```python
class ListenerManager(QObject):
    """
    ListenerManager is a UDP listener manager.
    It manages a configurable set of Listeners for supported ASIC cryptominers
    and forwards validated IP reports.

    Args:
        parent (QObject) : The parent object.

    Signals:
        report_received (IPReport) : emits IPReport when a Listener receives a IP report result.
        error_received (ListenerError) : emits a ListenerError when a socket error occurred on a Listener.
        bind_failed (ListenerError) : emits a ListenerError when a Listener fails to bind.
    """

    # Signals
    report_received: Signal = Signal(IPReport)
    error_received: Signal = Signal(ListenerError)
    bind_failed: Signal = Signal(ListenerError)
```
