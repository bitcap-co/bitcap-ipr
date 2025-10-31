from enum import Enum


class PortType(Enum):
    COMMON = 14235
    ICERIVER = 11503
    WHATSMINER = 8888
    SEALMINER = 18650
    GOLDSHELL = 1314
    ELPHAPEX = 9999
    UNKNOWN = 0

    @classmethod
    def from_port(cls, port: int):
        return cls(port)


ZLIB_DEFAULT_MAGIC = b"\x78\x9c"
IP_PATTERN = (
    r"((25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)(\.)){3}(25[0-5]|2[0-4]\d|1\d{2}|[1-9]?\d)"
)
MAC_PATTERN = r"([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})"
