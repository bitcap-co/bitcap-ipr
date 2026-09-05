import json
import logging
from typing import Literal, final, override

import httpx
from pydantic import ValidationError

from mod.ipr_asic import settings
from mod.ipr_asic.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)
from mod.ipr_asic.protocol import BaseHTTPClient
from mod.ipr_asic.schemas.auradine import (
    LED,
    CGMinerResponse,
    IPReport,
    MinerPasswdConfig,
    Mode,
    ModeResponse,
    NetworkInfo,
    Pool,
    Summary,
)
from mod.ipr_asic.schemas.models import (
    APIObject,
    BlinkStatus,
    MinerPoolConfig,
    PoolConfig,
)

logger = logging.getLogger(__name__)


@final
class AuradineHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 8080,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, transport=transport)

        self.username: str = "admin"
        if alt_pwd:
            settings.set_alt_auth("auradine", alt_pwd)
        self.passwds: list[str] = settings.get_auth_list("auradine")

        self.command_path: str = "{command}"
        self.token: str | None = None

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

    @override
    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            data = f'{{"command":"token","user":"{self.username}","password":"{pwd}"}}'
            try:
                async with self._new_client() as client:
                    resp = await client.post(self.base_url + "token", data=data)
                    _ = resp.raise_for_status()
            except (httpx.ConnectError, httpx.TimeoutException):
                raise FailedConnectionError("Failed to connect or timeout occurred")
            except httpx.HTTPError:
                continue
            else:
                if resp.status_code == 200:
                    try:
                        resobj = resp.json()
                        valid = self._validate_response(resobj)
                    except (
                        json.JSONDecodeError,
                        APIError,
                    ):
                        break
                    else:
                        if not valid.token or len(valid.token) != 1:
                            continue
                        self.authed = True
                        self.pwd = pwd
                        self.token = valid.token[0].token
                        break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    async def get_hostname(self) -> str:
        resp = await self.get_system_info()
        return resp.hostname

    async def get_mac_addr(self) -> str:
        resp = await self.get_system_info()
        return resp.mac

    async def get_api_version(self) -> str:
        resp = await self.get_system_info()
        return resp.version

    async def get_system_info(self) -> IPReport:
        resp = await self.send_command("GET", command="ipreport2")
        valid = self._validate_response(resp)
        if valid.ip_report is None or len(valid.ip_report) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.ip_report[0]

    async def get_network_info(self) -> NetworkInfo:
        resp = await self.send_command("GET", command="network")
        valid = self._validate_response(resp)
        if valid.network is None or len(valid.network) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.network[0]

    async def summary(self) -> Summary:
        resp = await self.send_command("GET", command="summary")
        valid = self._validate_response(resp)
        if valid.summary is None or len(valid.summary) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.summary[0]

    async def get_miner_conf(self) -> ModeResponse:
        resp = await self.send_command("GET", command="mode")
        valid = self._validate_response(resp)
        if valid.mode is None or len(valid.mode) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.mode[0]

    async def set_miner_conf(self, conf: APIObject) -> APIObject:
        try:
            mode = Mode.model_validate(conf)
        except ValidationError:
            raise APIError("Invalid Mode")
        else:
            resp = await self.send_command(
                "POST",
                command="mode",
                payload=mode.model_dump(by_alias=True, exclude_none=True),
            )
            valid = self._validate_response(resp)
            if valid.mode is None or len(valid.mode) != 1:
                raise APIInvalidResponse(reason="malformed")
            return valid.mode[0].model_dump()

    async def pools(self) -> list[Pool]:
        resp = await self.send_command("GET", command="pools")
        valid = self._validate_response(resp)
        if valid.pools is None:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.pools

    async def get_pool_conf(self) -> PoolConfig:
        pools = await self.pools()
        pool_conf: list[MinerPoolConfig] = []
        for pool in pools:
            pool_conf.append(
                MinerPoolConfig(url=pool.url, user=pool.user, pwd=pool.passwd)
            )
        return PoolConfig(pool_conf)

    async def get_whitelisted_pools(self) -> APIObject:
        resp = await self.send_command("GET", command="whitelistpools")
        valid = self._validate_response(resp)
        if valid.whitelist_pools is None or len(valid.whitelist_pools) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.whitelist_pools[0].model_dump()

    async def get_miner_status(self) -> APIObject:
        resp = await self.send_command("GET", command="led")
        valid = self._validate_response(resp)
        if valid.led is None or len(valid.led) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.led[0].model_dump(by_alias=True, exclude_none=True)

    async def get_blink_status(self) -> BlinkStatus:
        resp = await self.send_command("GET", command="led")
        valid = self._validate_response(resp)
        if valid.led is None or len(valid.led) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            blink = BlinkStatus(
                blink=valid.led[0].code == 3
                or (valid.led[0].led1 == 4 and valid.led[0].led2 == 4)
            )
            return blink

    @override
    async def blink(
        self,
        enabled: bool,
    ) -> APIObject:
        led = LED(
            code=3 if enabled else 2,
        )
        resp = await self.send_command(
            "POST", command="led", payload=led.model_dump(exclude_none=True)
        )
        _ = self._validate_response(resp)
        return resp

    async def set_led(
        self, led1: int, led2: int, msg: str, code: int = 102
    ) -> APIObject:
        led = LED(code=code, led1=led1, led2=led2, msg=msg)
        resp = await self.send_command("POST", command="led", payload=led.model_dump())
        _ = self._validate_response(resp)
        return resp

    async def set_miner_mode(self, mode: Literal["on", "off"] = "on") -> APIObject:
        conf = {"sleep": mode}
        return await self.set_miner_conf(conf)

    @override
    async def start(self) -> APIObject:
        return await self.set_miner_mode(mode="off")

    @override
    async def stop(self) -> APIObject:
        return await self.set_miner_mode(mode="on")

    @override
    async def restart(self) -> APIObject:
        return await super().restart()

    @override
    async def reboot(self) -> APIObject:
        return await self.send_command(
            "POST", command="restart", payload={"command": "restart"}
        )

    @override
    async def update_passwd(self, old_passwd: str, new_passwd: str) -> APIObject:
        pw_conf = MinerPasswdConfig(user=self.username, old=old_passwd, new=new_passwd)
        resp = await self.send_command(
            "POST", command="password", payload=pw_conf.model_dump()
        )
        _ = self._validate_response(resp)
        return resp

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        pool_conf: list[dict[str, str]] = []
        for i in range(len(urls)):
            if not len(urls[i]) and not len(users[i]):
                continue
            pool_conf.append(
                MinerPoolConfig(url=urls[i], user=users[i], pwd=passwds[i]).model_dump(
                    by_alias=True
                )
            )
        pools = {"command": "updatepools", "pools": pool_conf}
        resp = await self.send_command("POST", command="updatepools", payload=pools)
        valid = self._validate_response(resp)
        if valid.update_pools is None or len(valid.update_pools) != 1:
            raise APIInvalidResponse(reason="malformed")
        return resp
