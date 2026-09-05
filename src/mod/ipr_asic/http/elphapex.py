# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from typing import final, override

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
from mod.ipr_asic.schemas.antminer import (
    ActionResult,
    MinerPasswdConfig,
    NetworkInfo,
    SystemInfo,
)
from mod.ipr_asic.schemas.elphapex import (
    MinerConfig,
    MinerPool,
    MinerSummary,
    PoolsResponse,
    SummaryResponse,
)
from mod.ipr_asic.schemas.models import (
    APIObject,
    BlinkStatus,
    ContentResponse,
    PoolConfig,
)

logger = logging.getLogger(__name__)


@final
class ElphapexHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, alt_pwd, transport)

        self.username: str = "root"
        if alt_pwd:
            settings.set_alt_auth("elphapex", alt_pwd)
        self.passwds: list[str] = settings.get_auth_list("elphapex")

        self.command_path: str = "cgi-bin/{command}.cgi"

    @override
    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            digest = httpx.BasicAuth(self.username, pwd)
            try:
                async with self._new_client(auth=digest) as client:
                    resp = await client.get(self.base_url)
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
                    self.authed = True
                    self.digest = digest
                    self.pwd = pwd
                    break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    async def get_hostname(self) -> str:
        resp = await self.get_system_info()
        return resp.hostname

    async def get_mac_addr(self) -> str:
        resp = await self.get_system_info()
        return resp.macaddr

    async def get_system_info(self) -> SystemInfo:
        resp = await self.send_command("GET", command="get_system_info")
        try:
            resobj = SystemInfo.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_network_info(self) -> NetworkInfo:
        resp = await self.send_command("GET", command="get_network_info")
        try:
            resobj = NetworkInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def log(self, num: int = -1) -> ContentResponse:
        """Get miner log

        Args:
        num: get history log number. -1 is current log
        """
        resp = await self.send_command(
            "GET", command="hlog", payload={"key": "log", "body": {"num": num}}
        )
        try:
            resobj = ContentResponse.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def summary(self) -> MinerSummary:
        resp = await self.send_command("GET", command="summary")
        try:
            resobj = SummaryResponse.model_validate(obj=resp, by_alias=True)
        except (ValidationError, ValueError) as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.summary[0]

    async def get_miner_conf(self) -> MinerConfig:
        resp = await self.send_command("GET", command="get_miner_conf")
        try:
            resobj = MinerConfig.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def set_miner_conf(self, conf: APIObject) -> APIObject:
        resp = await self.send_command("POST", command="set_miner_conf", payload=conf)
        try:
            resobj = ActionResult.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            err = resobj.error()
            if err:
                logger.error(f"{self.__repr__()} : {err}")
                raise APIError("Command failed!")
            return resobj.model_dump(exclude_none=True)

    async def pools(self) -> list[MinerPool]:
        resp = await self.send_command("GET", command="pools")
        try:
            resobj = PoolsResponse.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.pools

    async def get_pool_conf(self) -> PoolConfig:
        resp = await self.get_miner_conf()
        return resp.pools

    async def get_blink_status(self) -> BlinkStatus:
        resp = await self.send_command("GET", command="get_blink_status")
        try:
            resobj = BlinkStatus.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    @override
    async def blink(self, enabled: bool) -> APIObject:
        blink = BlinkStatus(blink=enabled)
        payload = blink.model_dump(mode="json")
        return await self.send_command("POST", command="blink", payload=payload)

    @override
    async def restart(self) -> APIObject:
        return await self.reboot()

    @override
    async def reboot(self) -> APIObject:
        return await self.send_command("POST", command="reboot")

    @override
    async def update_passwd(self, old_passwd: str, new_passwd: str) -> APIObject:
        pw_conf = MinerPasswdConfig(
            curr_passwd=old_passwd, new_passwd=new_passwd, confirm_passwd=new_passwd
        )
        return await self.send_command(
            "POST",
            command="passwd",
            payload=pw_conf.model_dump(mode="json", by_alias=True),
        )
        # try:
        #     resobj = ActionResponse.model_validate(obj=resp)
        # except ValidationError as e:
        #     logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
        #     raise APIInvalidResponse
        # else:
        #     err = resobj.error()
        #     if err:
        #         logger.error(f"{self.__repr__()} : {err}")
        #         raise APIError("Command failed!")
        #     return resobj.model_dump(exclude_none=True)

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        conf = await self.get_miner_conf()
        ta = TypeAdapter(PoolConfig)
        pool_conf: list[dict[str, str]] = ta.dump_python(conf.pools, by_alias=True)

        for i in range(len(urls)):
            if (
                not any(pool_conf[i].values())
                and not len(urls[i])
                and not len(users[i])
            ):
                continue
            pool_conf[i] = {
                "url": urls[i],
                "user": users[i],
                "pass": passwds[i],
            }

        conf.pools = ta.validate_python(pool_conf)

        new_conf = conf.model_dump(mode="json", by_alias=True, exclude_none=True)
        return await self.set_miner_conf(conf=new_conf)
