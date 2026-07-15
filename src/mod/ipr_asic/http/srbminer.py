# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from string import Template

import httpx
from pydantic import BaseModel, ValidationError

from mod.ipr_asic.errors import APIError, APIInvalidResponse
from mod.ipr_asic.protocol import BaseHTTPClient

logger = logging.getLogger(__name__)


class GPUDevice(BaseModel):
    device: str = ""
    vendor: str = ""
    model: str = ""


class SRBPool(BaseModel):
    pool: str = ""
    wallet: str = ""


class SRBAlgorithm(BaseModel):
    name: str = ""
    pool: SRBPool = SRBPool()


class SRBMinerInfo(BaseModel):
    rig_name: str = ""
    miner_version: str = ""
    mining_time: int = 0
    total_cpu_workers: int = 0
    total_gpu_workers: int = 0
    gpu_devices: list[GPUDevice] = []
    algorithms: list[SRBAlgorithm] = []


class SRBMinerHTTPClient(BaseHTTPClient):
    """HTTP client for HiveOS GPU rigs via the SRBMiner-MULTI remote API.

    SRBMiner exposes a read-only JSON status endpoint on port 21550 by default.
    The API is unauthenticated, so requests are issued directly.
    """

    def __init__(
        self,
        ip: str,
        port: int = 21550,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, alt_pwd, transport)
        # SRBMiner's remote API is read-only and unauthenticated.
        self.authed = True
        self.command_path = Template("${command}")

    async def authenticate(self) -> None:
        # nothing to authenticate against; the API is open.
        self.authed = True

    async def get_hostname(self) -> str:
        return (await self.get_system_info())["rig_name"]

    async def get_mac_addr(self) -> str:
        # not exposed by the SRBMiner API; MAC comes from the IP Report.
        return await super().get_mac_addr()

    async def get_api_version(self) -> str:
        return (await self.get_system_info())["miner_version"]

    async def get_system_info(self) -> dict:
        resp = await self.send_command("GET", command="")
        try:
            info = SRBMinerInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return info.model_dump()

    async def get_network_info(self) -> dict:
        return await super().get_network_info()

    async def log(self, *args, **kwargs) -> dict:
        return await super().log(*args, **kwargs)

    async def summary(self) -> dict:
        return await self.get_system_info()

    async def get_miner_conf(self) -> dict:
        return await super().get_miner_conf()

    async def set_miner_conf(self, *args, **kwargs) -> dict:
        return await super().set_miner_conf(*args, **kwargs)

    async def pools(self) -> list[dict]:
        info = await self.get_system_info()
        pools: list[dict] = []
        for algo in info["algorithms"]:
            pool = algo["pool"]
            if pool["pool"]:
                pools.append({"url": pool["pool"], "user": pool["wallet"]})
        return pools

    async def get_pool_conf(self) -> list[dict]:
        return await self.pools()

    async def get_miner_status(self) -> dict:
        return await super().get_miner_status()

    async def get_blink_status(self) -> dict:
        return await super().get_blink_status()

    async def blink(self, enabled: bool, *args, **kwargs) -> dict:
        # GPU rigs have no locate LED to toggle.
        raise APIError("Locate is not supported for HiveOS GPU rigs")

    async def set_miner_mode(self, *args, **kwargs) -> dict:
        return await super().set_miner_mode(*args, **kwargs)

    async def start(self) -> dict:
        raise APIError("Start is not supported for HiveOS GPU rigs")

    async def stop(self) -> dict:
        raise APIError("Stop is not supported for HiveOS GPU rigs")

    async def restart(self) -> dict:
        raise APIError("Restart is not supported for HiveOS GPU rigs")

    async def reboot(self) -> dict:
        raise APIError("Reboot is not supported for HiveOS GPU rigs")

    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        raise APIError("Pool configuration is not supported for HiveOS GPU rigs")
