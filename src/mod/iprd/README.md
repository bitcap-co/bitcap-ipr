## iprd module
[IPR Daemon](https://github.com/bitcap-co/ipr-daemon) integration.

### Overview
IPR Daemon (iprd) is an standalone IP report listening backend that listens live on the wire across a facility's network. IP report messages are written to a subscribable TCP stream with a configurable endpoint for easy reading/integration with front-ends/applications.

### Structure
The iprd module consists of the following components:
 - `IPRDListener` - QTcpSocket listener that subscribes to a running IPR Daemon TCP stream and emits signals when new data is available.
 - `IPRDSocket` - QTcpSocket handler for iprd that facilitates sending commands to a running IPR Daemon instance (i.e. sending 'iprd_status' to get the daemon's status/health)
 - `IPRDServiceListener` - QObject-based Zeroconf service listener that discovers running IPR Daemon instances on the network via mDNS/DNS-SD. Emits signals when new services are found/updated/removed.
 - `IPRDController` - High-level state machine that coordinates network monitoring, service discovery, endpoint selection, and the `IPRDListener` lifecycle. It supports discovered and manually configured endpoints, handles suspend/resume and network changes, forwards received reports, and retries failed connections based on current endpoint mode policy.
