# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import logging
import re
from typing import Literal, final, override

import httpx
from pydantic import TypeAdapter, ValidationError

from mod.ipr_asic import settings
from mod.ipr_asic.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)
from mod.ipr_asic.protocol import BaseHTTPClient
from mod.ipr_asic.schemas.models import (
    APIObject,
    BlinkStatus,
    ContentResponse,
    PoolConfig,
)
from mod.ipr_asic.schemas.vnish import (
    Info,
    MinerPasswdConfig,
    MinerStatus,
    NetworkInfo,
    PoolStats,
    Settings,
    SettingsResponse,
    Summary,
    VnishError,
)

logger = logging.getLogger(__name__)

_VERSION_RE = re.compile(r"(\d+(?:\.\d+)*)")


def _parse_version_int(version: str) -> int:
    if not version:
        return 0
    match = _VERSION_RE.match(version)
    if not match:
        return 0
    return int(match.group(1).replace(".", ""))


@final
class VnishHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, alt_pwd, transport)

        self.username: str = "admin"
        if alt_pwd:
            settings.set_alt_auth("vnish", alt_pwd)
        self.passwds: list[str] = settings.get_auth_list("vnish")

        self.command_path: str = "api/v1/{command}"

    @override
    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            try:
                async with self._new_client() as client:
                    resp = await client.post(
                        self.base_url + "api/v1/unlock", json={"pw": pwd}
                    )
                    _ = resp.raise_for_status()
            except (
                httpx.ConnectError,
                httpx.TimeoutException,
            ):
                raise FailedConnectionError("Failed to connect or timeout occurred")
            except httpx.HTTPError:
                continue
            else:
                if resp.status_code == 200:
                    try:
                        resobj = resp.json()
                    except json.JSONDecodeError:
                        break
                    else:
                        if "token" in resobj:
                            self.authed = True
                            self.token = resobj["token"]
                            self.pwd = pwd
                            break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    async def get_hostname(self) -> str:
        resp = await self.get_network_info()
        return resp.hostname

    async def get_mac_addr(self) -> str:
        resp = await self.get_network_info()
        return resp.mac

    async def get_api_version(self) -> str:
        resp = await self.get_system_info()
        return resp.fw_version

    async def get_system_info(self) -> Info:
        resp = await self.send_command("GET", command="info")
        try:
            resobj = Info.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_network_info(self) -> NetworkInfo:
        resp = await self.get_system_info()
        return resp.system.network_status

    async def log(
        self, log_type: Literal["status", "miner", "autotune", "system", "messages"]
    ) -> ContentResponse:
        resp = await self.send_command("GET", command=f"logs/{log_type}")
        try:
            resobj = ContentResponse.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def summary(self) -> Summary:
        resp = await self.send_command("GET", command="summary")
        try:
            resobj = Summary.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_miner_conf(self) -> Settings:
        resp = await self.send_command("GET", command="settings")
        try:
            resobj = Settings.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def set_miner_conf(self, conf: APIObject) -> APIObject:
        resp = await self.send_command("POST", command="settings", payload=conf)
        try:
            resobj = SettingsResponse.model_validate(obj=resp)
        except ValidationError:
            try:
                resobj = VnishError.model_validate(obj=resp)
            except ValidationError as e:
                logger.error(
                    f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}"
                )
                raise APIInvalidResponse
            else:
                logger.error(
                    f"{self.__repr__()} : received API error {resobj.as_str()}"
                )
                raise APIError("Command failed!")
        else:
            return resobj.model_dump()

    async def pools(self) -> list[PoolStats]:
        resp = await self.summary()
        return resp.miner.pools

    async def get_pool_conf(self) -> PoolConfig:
        resp = await self.get_miner_conf()
        if resp.miner is not None:
            return resp.miner.pools
        return PoolConfig([])

    async def get_miner_status(self) -> MinerStatus:
        resp = await self.send_command("GET", command="status")
        try:
            resobj = MinerStatus.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_blink_status(self) -> BlinkStatus:
        resp = await self.get_miner_status()
        blink = BlinkStatus(blink=resp.find_miner)
        return blink

    @override
    async def blink(self, enabled: bool) -> APIObject:
        ver = await self.get_api_version()
        version = _parse_version_int(ver)
        if version >= 133:
            return await self.send_command(
                "POST", command="locate-miner", payload={"is_enabled": enabled}
            )
        else:
            return await self.send_command("POST", command="find-miner")

    @override
    async def start(self) -> APIObject:
        return await self.send_command("POST", command="mining/start")

    @override
    async def stop(self) -> APIObject:
        return await self.send_command("POST", command="mining/stop")

    @override
    async def restart(self) -> APIObject:
        return await self.send_command("POST", command="mining/restart")

    @override
    async def reboot(self) -> APIObject:
        return await self.send_command("POST", command="system/reboot")

    @override
    async def update_passwd(self, old_passwd: str, new_passwd: str) -> APIObject:
        pw_conf = MinerPasswdConfig(curr_passwd=old_passwd, new_passwd=new_passwd)
        return await self.set_miner_conf(conf=pw_conf.model_dump(by_alias=True))

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        ta = TypeAdapter(PoolConfig)
        conf = await self.get_miner_conf()
        if conf.miner is None:
            raise APIError("Failed to retrieve miner config.")
        pool_conf: list[dict[str, str]] = ta.dump_python(conf.miner.pools)
        for i in range(len(urls)):
            if (
                not any(pool_conf[i].values())
                and not len(urls[i])
                and not len(users[i])
            ):
                continue
            pool_conf[i] = {"url": urls[i], "user": users[i], "pass": passwds[i]}

        conf.miner.pools = ta.validate_python(pool_conf)
        new_conf = conf.model_dump(mode="json", by_alias=True, exclude_none=True)
        return await self.set_miner_conf(conf=new_conf)
