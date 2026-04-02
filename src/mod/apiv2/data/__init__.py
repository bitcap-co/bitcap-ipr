from datetime import datetime, timezone
from enum import Enum
from typing import Any, Self

from pydantic import BaseModel, Field


class MinerType(str, Enum):
    UNKNOWN = "unknown"
    ANTMINER = "antminer"
    ICERIVER = "iceriver"
    WHATSMINER = "whatsminer"
    SEALMINER = "sealminer"
    GOLDSHELL = "goldshell"
    VOLCMINER = "volcminer"
    HAMMER = "hammer"
    ELPHAPEX = "elphapex"
    LUX_OS = "luxor"
    VNISH = "vnish"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, type: str):
        try:
            return cls(type.lower())
        except ValueError:
            return MinerType.UNKNOWN


class MinerFirmware(str, Enum):
    UNKNOWN = "Unknown"
    STOCK = "Stock"
    VNISH = "Vnish"
    LUX_OS = "LuxOS"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, fw_type: str):
        try:
            return cls(fw_type)
        except ValueError:
            return MinerFirmware.UNKNOWN


class MinerAlgorithm(str, Enum):
    SHA256 = "SHA256"
    SCRYPT = "Scrypt"
    KHEAVYHASH = "KHeavyHash"
    KADENA = "Kadena"
    HANDSHAKE = "Handshake"
    X11 = "X11"
    BLAKE256 = "Blake256"
    BLAKE3 = "Blake3"
    EAGLESONG = "Eaglesong"
    ETHASH = "EtHash"
    EQUIHASH = "Equihash"
    RANDOMX = "RandomX"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, algo: str) -> Self | None:
        try:
            return cls(algo)
        except ValueError:
            for enum in list(cls):
                if algo.lower() == enum.name.lower() or algo.lower().__contains__(
                    enum.name.lower()
                ):
                    return enum
            return None


class MinerPlatform(str, Enum):
    XILINX = "Xilinx"
    BEAGLEBONE = "BeagleBone"
    AMLOGIC = "AMLogic"
    CVITEK = "CVITEK"
    STM = "STM"

    def __str__(self) -> str:
        return self.value

    @classmethod
    def from_value(cls, platform: str) -> Self | None:
        try:
            return cls(platform)
        except ValueError:
            for enum in list(cls):
                if platform.lower() == enum.name.lower():
                    return cls(enum.value)
            return None


class MinerData(BaseModel):
    ip: str | None = None
    created_at: datetime = Field(
        exclude=True, default_factory=datetime.now(timezone.utc).astimezone, repr=False
    )

    type: MinerType | None = None
    subtype: str | None = None
    firmware: MinerFirmware | None = None
    algorithm: MinerAlgorithm | None = None
    platform: MinerPlatform | str | None = None
    serial: str | None = None
    mac: str | None = None
    api_version: str | None = None
    fw_version: str | None = None
    hostname: str | None = None
    uptime: int | None = None
    stratum_url: str | None = None
    username: str | None = None
    worker_name: str | None = None

    def as_dict(self) -> dict[str, Any]:
        miner_data = self.model_dump()
        for key in miner_data.keys():
            # fill missing keys
            if miner_data[key] is None or miner_data[key] == "":
                miner_data[key] = "N/A"
            # serialize enums
            if isinstance(miner_data[key], Enum):
                miner_data[key] = miner_data[key].__str__()
        return miner_data


from .base import BaseParser
from .models import ActionResponse, BlinkStatus, MinerConfPool
