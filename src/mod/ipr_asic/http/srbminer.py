# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from typing import final, override

import httpx
from pydantic import ValidationError

from mod.ipr_asic.errors import APIInvalidResponse
from mod.ipr_asic.protocol import BaseHTTPClient
from mod.ipr_asic.schemas.models import PoolConfig, SummaryModel
from mod.ipr_asic.schemas.srbminer import SRBMinerInfo, SRBPool

logger = logging.getLogger(__name__)


class SRBMinerHTTPClient(BaseHTTPClient):
    """HTTP client for HiveOS GPU rigs via the SRBMiner-MULTI remote API.

    SRBMiner exposes a read-only JSON status endpoint on port 21550 by default.
    The API is unauthenticated, so requests are issued directly.
    """

    @final
    def __init__(
        self,
        ip: str,
        port: int = 21550,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, alt_pwd, transport)
        # SRBMiner's remote API is read-only and unauthenticated.
        self.authed: bool = True
        self.command_path: str = "{command}"

    @override
    async def authenticate(self) -> None:
        # nothing to authenticate against; the API is open.
        self.authed = True

    async def get_hostname(self) -> str:
        return (await self.get_system_info()).rig_name

    # async def get_mac_addr(self) -> str:
    #     # not exposed by the SRBMiner API; MAC comes from the IP Report.
    #     return await super().get_mac_addr()

    async def get_api_version(self) -> str:
        return (await self.get_system_info()).miner_version

    async def get_system_info(self) -> SRBMinerInfo:
        resp = await self.send_command("GET", command="")
        try:
            info = SRBMinerInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return info

    async def summary(self) -> SummaryModel:
        # not exposed by SRBMiner API
        return SummaryModel()

    async def pools(self) -> list[SRBPool]:
        info = await self.get_system_info()
        pools: list[SRBPool] = []
        for algo in info.algorithms:
            pool = algo.pool
            if pool.pool:
                pools.append(SRBPool(pool=pool.pool, wallet=pool.wallet))
        return pools

    async def get_pool_conf(self) -> PoolConfig:
        # not exposed by SRBMiner API
        return PoolConfig(root=[])
