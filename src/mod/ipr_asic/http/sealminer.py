# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import hashlib
import json
import logging
import random
import time
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
from mod.ipr_asic.schemas.models import APIObject, BlinkStatus, PoolConfig
from mod.ipr_asic.schemas.sealminer import (
    ActionResult,
    ConfigResult,
    LoginResponse,
    MinerConfig,
    MinerPasswdConfig,
    MinerPool,
    NetworkInfo,
    Summary,
    SystemInfo,
)

logger = logging.getLogger(__name__)


def gen_php_session_id() -> str:
    random.seed(time.time_ns())
    ran_id = bytearray(random.randbytes(10))

    h = hashlib.new("sha1", data=ran_id)
    return h.hexdigest()[:26]


@final
class SealminerHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, alt_pwd, transport)

        self.username: str = "seal"
        if alt_pwd:
            settings.set_alt_auth("sealminer", alt_pwd)
        self.passwds: list[str] = settings.get_auth_list("sealminer")

        self.command_path: str = "cgi-bin/{command}.php"

    @override
    async def authenticate(self) -> None:
        php_session = gen_php_session_id()
        headers = {"Cookie": "userLanguage=en; PHPSESSID=" + php_session}
        for pwd in self.passwds:
            if not pwd:
                continue
            data = {"username": self.username, "origin_pwd": pwd}
            try:
                resp = await self._do_http(
                    method="POST", headers=headers, path="cgi-bin/login.php", data=data
                )
                _ = resp.raise_for_status()
            except (httpx.ConnectError, httpx.TimeoutException):
                raise FailedConnectionError("Failed to connect or timeout occurred")
            except httpx.HTTPError:
                continue
            else:
                if resp.status_code == 200:
                    try:
                        resobj = resp.json()
                        login_response = LoginResponse.model_validate(obj=resobj)
                    except (json.JSONDecodeError, ValidationError):
                        break
                    else:
                        if login_response.state != 0:
                            continue
                        self.cookies = (
                            "username=seal; userLanguage=en; PHPSESSID=" + php_session
                        )
                        self.authed = True
                        self.pwd = pwd
                        break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    # async def get_hostname(self) -> str:
    #     return await super().get_hostname()

    async def get_mac_addr(self) -> str:
        resp = await self.get_system_info()
        return resp.macaddr

    # async def get_api_version(self) -> str:
    #     return await super().get_api_version()

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

    async def summary(self) -> Summary:
        resp = await self.send_command("GET", command="miner-status")
        try:
            resobj = Summary.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_miner_conf(self) -> MinerConfig:
        resp = await self.send_command("GET", command="get_miner_poolconf")
        try:
            resobj = MinerConfig.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def set_miner_conf(self, conf: APIObject) -> APIObject:
        resp = await self.send_command(
            "POST", command="set_miner_poolconf", payload=conf
        )
        try:
            resobj = ConfigResult.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            err = resobj.error()
            if err:
                logger.error(f"{self.__repr__()} : {err}")
                raise APIError("Command failed!")
            return resobj.model_dump()

    async def pools(self) -> list[MinerPool]:
        resp = await self.summary()
        return resp.pools

    async def get_pool_conf(self) -> PoolConfig:
        resp = await self.get_miner_conf()
        return resp.pools

    async def get_blink_status(self) -> BlinkStatus:
        resp = await self.get_system_info()
        blink = BlinkStatus(blink=resp.led == "on")
        return blink

    @override
    async def blink(self, enabled: bool) -> APIObject:
        data = f'{{"key":"led","value":"{"on" if enabled else "off"}"}}'
        return await self.send_command("POST", command="led_conf", data=data)

    async def set_miner_mode(self, mode: int = 1) -> APIObject:
        data = f'{{"params_data":{mode}}}'
        resp = await self.send_command("POST", command="mining_setting", data=data)
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
            return resobj.model_dump()

    @override
    async def start(self) -> APIObject:
        return await self.set_miner_mode(mode=1)

    @override
    async def stop(self) -> APIObject:
        return await self.set_miner_mode(mode=0)

    @override
    async def restart(self) -> APIObject:
        return await self.start()

    @override
    async def reboot(self) -> APIObject:
        return await self.send_command("POST", command="reboot")

    @override
    async def update_passwd(self, old_passwd: str, new_passwd: str) -> APIObject:
        pw_conf = MinerPasswdConfig(
            username=self.username,
            curr_passwd=old_passwd,
            new_passwd=new_passwd,
            confirm_passwd=new_passwd,
        )
        return await self.send_command(
            "POST", command="update_passwd", payload=pw_conf.model_dump(by_alias=True)
        )

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        conf = await self.get_miner_conf()
        ta = TypeAdapter(PoolConfig)
        pool_conf: list[dict[str, str]] = ta.dump_python(conf.pools)

        new_conf = {
            "poolurl1": "",
            "pooluser1": "",
            "poolpwd1": "",
            "poolurl2": "",
            "pooluser2": "",
            "poolpwd2": "",
            "poolurl3": "",
            "pooluser3": "",
            "poolpwd3": "",
        }
        for i in range(len(urls)):
            if (
                not any(pool_conf[i].values())
                and not len(urls[i])
                and not len(users[i])
            ):
                continue
            idx = i + 1
            new_conf[f"poolurl{idx}"] = urls[i]
            new_conf[f"pooluser{idx}"] = users[i]
            new_conf[f"poolpwd{idx}"] = passwds[i]
        return await self.set_miner_conf(conf=new_conf)
