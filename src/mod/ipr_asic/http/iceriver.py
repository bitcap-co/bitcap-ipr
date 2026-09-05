# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import logging
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
from mod.ipr_asic.schemas.iceriver import (
    ActionResult,
    MinerConfig,
    MinerPool,
    NetworkInfo,
    UserPanel,
)
from mod.ipr_asic.schemas.models import (
    APIObject,
    BlinkStatus,
    MinerPoolConfig,
    PoolConfig,
)

logger = logging.getLogger(__name__)


@final
class IceriverHTTPClient(BaseHTTPClient):
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
            settings.set_alt_auth("iceriver", alt_pwd)
        self.passwds: list[str] = settings.get_auth_list("iceriver")

        self.command_path: str = "user/{command}"

    @override
    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            try:
                async with self._new_client() as client:
                    resp = await client.post(
                        self.base_url + "user/loginpost",
                        data={"post": 6, "user": self.username, "pwd": pwd},
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
                        action_resp = ActionResult(**resobj)
                    except (json.JSONDecodeError, ValidationError):
                        break
                    else:
                        err = action_resp.error_()
                        if err:
                            continue
                        self.authed = True
                        self.pwd = pwd
                        break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    async def get_hostname(self) -> str:
        resp = await self.get_network_info()
        return resp.host

    async def get_mac_addr(self) -> str:
        resp = await self.get_network_info()
        return resp.mac

    async def get_system_info(self) -> UserPanel:
        return await self.summary()

    async def get_network_info(self) -> NetworkInfo:
        resp = await self.send_command("POST", command="ipconfig", data={"post": 1})
        try:
            resobj = NetworkInfo.model_validate(obj=resp["data"])
        except (ValidationError, KeyError) as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def summary(self) -> UserPanel:
        resp = await self.send_command("POST", command="userpanel", data={"post": 4})
        try:
            resobj = UserPanel.model_validate(obj=resp["data"], by_alias=True)
        except (ValidationError, KeyError) as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_miner_conf(self) -> MinerConfig:
        resp = await self.send_command(
            "POST", command="machineconfig", data={"post": 1}
        )
        try:
            resobj = MinerConfig.model_validate(obj=resp["data"], by_alias=True)
        except (ValidationError, KeyError) as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def set_miner_conf(self, conf: APIObject) -> APIObject:
        resp = await self.send_command("POST", command="machineconfig", data=conf)
        try:
            resobj = ActionResult.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            err = resobj.error_()
            if err:
                logger.error(f"{self.__repr__()} : {err}")
                raise APIError("Command failed!")
            return resobj.model_dump()

    async def pools(self) -> list[MinerPool]:
        resp = await self.summary()
        return resp.pools

    async def get_pool_conf(self) -> PoolConfig:
        resp = await self.get_miner_conf()
        pool_conf: list[MinerPoolConfig] = []
        for pool in resp.pools:
            pool_conf.append(
                MinerPoolConfig(url=pool.addr, user=pool.user, pwd=pool.passwd)
            )
        return PoolConfig(pool_conf)

    async def get_blink_status(self) -> BlinkStatus:
        user = await self.summary()
        blink_status = BlinkStatus(blink=user.locate)
        return blink_status

    @override
    async def blink(self, enabled: bool) -> APIObject:
        data = {"post": 5, "locate": 1 if enabled else 0}
        resp = await self.send_command("POST", command="userpanel", data=data)
        try:
            resobj = ActionResult.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            err = resobj.error_()
            if err:
                logger.error(f"{self.__repr__()} : {err}")
                raise APIError("Command failed!")
            return resobj.model_dump()

    async def set_miner_mode(
        self, mode: Literal["normal", "sleep"] = "normal"
    ) -> APIObject:
        conf = await self.get_miner_conf()
        data: APIObject = {"post": 3}
        data["fanratio"] = f"{conf.ratio}"
        data["fanmode"] = mode
        pools = conf.pools
        for i, pool in enumerate(pools):
            idx = i + 1
            data[f"pool{idx}address"] = pool.addr
            data[f"pool{idx}miner"] = pool.user
            data[f"pool{idx}pwd"] = pool.passwd
        return await self.set_miner_conf(conf=data)

    @override
    async def start(self) -> APIObject:
        return await self.set_miner_mode(mode="normal")

    @override
    async def stop(self) -> APIObject:
        return await self.set_miner_mode(mode="sleep")

    @override
    async def restart(self) -> APIObject:
        return await self.reboot()

    @override
    async def reboot(self) -> APIObject:
        return await self.send_command("POST", command="userpanel", data={"post": 3})

    @override
    async def update_passwd(self, old_passwd: str, new_passwd: str) -> APIObject:
        data = {
            "post": 2,
            "nowpwd": old_passwd,
            "newpwd": new_passwd,
            "compwd": new_passwd,
        }
        resp = await self.send_command("POST", command="systemconfig", data=data)
        try:
            resobj = ActionResult.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            err = resobj.error_()
            if err:
                logger.error(f"{self.__repr__()} : {err}")
                raise APIError("Command failed!")
            return resobj.model_dump()

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        conf = await self.get_miner_conf()
        pool_conf = await self.get_pool_conf()
        ta = TypeAdapter(list[MinerPoolConfig])
        pools: list[dict[str, str]] = ta.dump_python(pool_conf.root)

        data: APIObject = {"post": 2}
        data["fanratio"] = f"{conf.ratio}"
        match conf.mode:
            case 0:
                data["fanmode"] = "sleep"
            case 1:
                data["fanmode"] = "normal"
            case _:
                data["fanmode"] = "normal"

        for i in range(len(urls)):
            if not any(pools[i].values()) and not len(urls[i]) and not len(users[i]):
                continue
            idx = i + 1
            data[f"pool{idx}address"] = urls[i]
            data[f"pool{idx}miner"] = users[i]
            data[f"pool{idx}pwd"] = passwds[i]
        return await self.set_miner_conf(conf=data)
