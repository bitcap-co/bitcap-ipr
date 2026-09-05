# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from typing import final, override

import httpx
from pydantic import (
    TypeAdapter,
    ValidationError,
)

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
    CGMinerResponse,
    MinerConfig,
    MinerPasswdConfig,
    MinerPool,
    MinerSummary,
    NetworkInfo,
    OldBlinkStatus,
    OldMinerPasswdConfig,
    OldMinerPool,
    PoolsResponse,
    SummaryResponse,
    SystemInfo,
)
from mod.ipr_asic.schemas.models import (
    APIObject,
    BlinkStatus,
    ContentResponse,
    MinerPoolConfig,
    PoolConfig,
)

logger = logging.getLogger(__name__)


@final
class AntminerHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, transport=transport)

        self.username: str = "root"
        if alt_pwd:
            settings.set_alt_auth("antminer", alt_pwd)
        self.passwds: list[str] = settings.get_auth_list("antminer")

        self.command_path: str = "cgi-bin/{command}.cgi"

    @override
    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            digest = httpx.DigestAuth(self.username, pwd)
            try:
                async with self._new_client(auth=digest) as client:
                    resp = await client.get(url=self.base_url)
                    _ = resp.raise_for_status()
            except (httpx.ConnectError, httpx.TimeoutException):
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

    async def get_api_version(self) -> str:
        resp = await self.get_system_info()
        return resp.cgminer_version or ""

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

    async def log(self) -> ContentResponse:
        resp = await self.send_command("GET", command="log")
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

    async def set_miner_mode(self, mode: int = 0) -> APIObject:
        resp = await self.get_miner_conf()
        resp.miner_mode = f"{mode}"

        return await self.set_miner_conf(
            conf=resp.model_dump(mode="json", by_alias=True, exclude_none=True)
        )

    @override
    async def start(self) -> APIObject:
        return await self.set_miner_mode(mode=0)

    @override
    async def stop(self) -> APIObject:
        return await self.set_miner_mode(mode=1)

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
        resp = await self.send_command(
            "POST",
            command="passwd",
            payload=pw_conf.model_dump(mode="json", by_alias=True),
        )
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


@final
class AntminerOldHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, transport=transport)

        self.username: str = "root"
        if alt_pwd:
            settings.set_alt_auth("antminer", alt_pwd)
        self.passwds: list[str] = settings.get_auth_list("antminer")

        self.command_path: str = "cgi-bin/{command}.cgi"

    @override
    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            digest = httpx.DigestAuth(self.username, pwd)
            try:
                async with self._new_client(auth=digest) as client:
                    resp = await client.get(url=self.base_url)
                    _ = resp.raise_for_status()
            except (httpx.ConnectError, httpx.TimeoutException):
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

    def _validate_response(self, data: APIObject) -> CGMinerResponse:
        try:
            resobj = CGMinerResponse.model_validate(obj=data, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            err = resobj.error()
            if err:
                logger.error(f"{self.__repr__()} : {APIError(err)!s}")
                raise APIError("Command failed!")
            return resobj

    async def get_hostname(self) -> str:
        resp = await self.get_system_info()
        return resp.hostname

    async def get_mac_addr(self) -> str:
        resp = await self.get_system_info()
        return resp.macaddr

    async def get_api_version(self) -> str:
        resp = await self.get_system_info()
        return resp.cgminer_version or ""

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

    async def log(self) -> ContentResponse:
        resp = await self.send_command("GET", command="get_kernel_log")
        try:
            resobj = ContentResponse.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def summary(self) -> MinerSummary:
        resp = await self.send_command("GET", command="miner_summary")
        valid = self._validate_response(resp)
        if valid.summary is None or len(valid.summary) != 1:
            raise APIInvalidResponse(reason="Malformed")
        else:
            try:
                return MinerSummary.model_validate(obj=valid.summary[0])
            except ValidationError as e:
                logger.error(
                    f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}"
                )
                raise APIInvalidResponse

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
        return await self.send_command("POST", command="set_miner_conf", data=conf)

    async def pools(self) -> list[OldMinerPool]:
        resp = await self.send_command("GET", command="miner_pools")
        valid = self._validate_response(resp)
        if valid.pools is None:
            raise APIInvalidResponse(reason="Malformed")
        else:
            return valid.pools

    async def get_pool_conf(self) -> PoolConfig:
        pools = await self.pools()
        pool_conf: list[MinerPoolConfig] = []
        for pool in pools:
            pool_conf.append(MinerPoolConfig(url=pool.url, user=pool.user))
        ta = TypeAdapter(PoolConfig)
        return ta.validate_python(pool_conf)

    async def get_blink_status(self) -> OldBlinkStatus:
        resp = await self.send_command(
            "GET", command="blink", data={"action": "onPageLoaded"}
        )
        try:
            resobj = OldBlinkStatus.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    @override
    async def blink(self, enabled: bool) -> APIObject:
        data = {"action": "startBlink" if enabled else "stopBlink"}
        return await self.send_command("POST", command="blink", data=data)

    @override
    async def restart(self) -> APIObject:
        return await self.reboot()

    @override
    async def reboot(self) -> APIObject:
        return await self.send_command("POST", command="reboot")

    @override
    async def update_passwd(self, old_passwd: str, new_passwd: str) -> APIObject:
        pw_conf = OldMinerPasswdConfig(
            curr_passwd=old_passwd, new_passwd=new_passwd, confirm_new_passwd=new_passwd
        )
        return await self.send_command(
            "POST",
            command="passwd",
            params=pw_conf.model_dump(mode="json", by_alias=True),
        )

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        conf = await self.get_miner_conf()

        data: APIObject = {}
        for i in range(len(urls)):
            data[f"_ant_pool{i + 1}url"] = urls[i]
            data[f"_ant_pool{i + 1}user"] = users[i]
            data[f"_ant_pool{i + 1}pw"] = passwds[i]

        data["_ant_nobeeper"] = "false"
        data["_ant_notempcontrol"] = "false"
        if conf.fan_ctrl:
            data["_ant_fan_customize_switch"] = "true"
            data["_ant_fan_customize_value"] = conf.fan_pwm
        else:
            data["_ant_fan_customize_switch"] = "false"
            data["_ant_fan_customize_value"] = ""
        data["_ant_freq"] = conf.freq

        return await self.set_miner_conf(conf=data)
