# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from collections.abc import Sequence
from typing import TypeVar

from pydantic import TypeAdapter, ValidationError

from mod.ipr_asic.errors import APIError, APIInvalidResponse
from mod.ipr_asic.protocol import BaseRPCClient
from mod.ipr_asic.schemas.cgminer import (
    BaseCGMinerResponse,
    BaseDev,
    BaseDevDetails,
    BasePool,
    BaseStat,
    BaseSummary,
    Version,
)
from mod.ipr_asic.schemas.models import (
    APIObject,
    MinerPoolConfig,
    PoolConfig,
    SystemInfoModel,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CGMinerRPCLayer(BaseRPCClient):
    def _validate_response(self, data: APIObject) -> str | None:
        try:
            resobj = BaseCGMinerResponse.model_validate(obj=data, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()}: {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.error()

    async def _get_one(
        self, command: str, response_key: str, adapter: TypeAdapter[T]
    ) -> T:
        resp = await self.send_command(command)
        error = self._validate_response(resp)
        if error is not None:
            logger.error(f"{self.__repr__()}: {APIError(error)!s}")
            raise APIError("Command failed")
        try:
            values = resp[response_key]
            if not isinstance(values, list) or len(values) != 1:
                raise APIInvalidResponse(reason=f"{response_key} must contain one item")
            return adapter.validate_python(values[0])
        except (KeyError, TypeError, ValidationError) as e:
            logger.error(f"{self.__repr__()}: {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse

    async def _get_many(
        self, command: str, response_key: str, adapter: TypeAdapter[list[T]]
    ) -> list[T]:
        resp = await self.send_command(command)
        error = self._validate_response(resp)
        if error is not None:
            logger.error(f"{self.__repr__()}: {APIError(error)!s}")
            raise APIError("Command failed")
        try:
            return adapter.validate_python(resp[response_key])
        except (KeyError, TypeError, ValidationError) as e:
            logger.error(f"{self.__repr__()}: {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse


class CGMinerRPCClient(CGMinerRPCLayer):
    async def version(self) -> Version:
        return await self._get_one("version", "VERSION", TypeAdapter(Version))

    async def summary(self) -> BaseSummary:
        return await self._get_one("summary", "SUMMARY", TypeAdapter(BaseSummary))

    async def stats(self) -> Sequence[BaseStat]:
        return await self._get_many("stats", "STATS", TypeAdapter(list[BaseStat]))

    async def devs(self) -> Sequence[BaseDev]:
        return await self._get_many("devs", "DEVS", TypeAdapter(list[BaseDev]))

    async def devdetails(self) -> Sequence[BaseDevDetails]:
        return await self._get_many(
            "devdetails", "DEVDETAILS", TypeAdapter(list[BaseDevDetails])
        )

    async def pools(self) -> Sequence[BasePool]:
        return await self._get_many("pools", "POOLS", TypeAdapter(list[BasePool]))

    async def get_system_info(self) -> SystemInfoModel:
        # generic CGMiner exposes no consolidated system-info command
        return SystemInfoModel()

    async def get_pool_conf(self) -> PoolConfig:
        pools = await self.pools()
        pool_conf: list[MinerPoolConfig] = []
        for pool in pools:
            pool_conf.append(MinerPoolConfig(url=pool.url, user=pool.user))
        return PoolConfig(pool_conf)
