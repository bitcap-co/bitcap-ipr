import logging
from html.parser import HTMLParser
from typing import final, override

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
from src.mod.ipr_asic.schemas.ipollo import (
    MinerConfig,
    MinerConfigPool,
    MinerPasswdConfig,
    MinerPool,
    MinerStatus,
    NetworkInfo,
    SystemInfo,
)
from src.mod.ipr_asic.schemas.models import ActionResultModel, APIObject, PoolConfig

logger = logging.getLogger(__name__)


class _MinerConfigHTMLParser(HTMLParser):
    """Extract LuCI cgminer configuration values from form controls."""

    field_prefix = "cbid.cgminer.default."

    def __init__(self) -> None:
        super().__init__()
        self.values: dict[str, str] = {}
        self._select_name: str | None = None

    @override
    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)

        if tag == "input":
            name = attributes.get("name") or attributes.get("id")
            value = attributes.get("value")
            if name and name.startswith(self.field_prefix) and value is not None:
                self.values[name] = value
        elif tag == "select":
            name = attributes.get("name") or attributes.get("id")
            self._select_name = (
                name if name and name.startswith(self.field_prefix) else None
            )
        elif tag == "option" and self._select_name and "selected" in attributes:
            value = attributes.get("value")
            if value is not None:
                self.values[self._select_name] = value

    @override
    def handle_endtag(self, tag: str) -> None:
        if tag == "select":
            self._select_name = None


@final
class IPolloHTTPClient(BaseHTTPClient):
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
            settings.set_alt_auth("ipollo", alt_pwd)
        self.passwds: list[str] = settings.get_auth_list("ipollo")

        self.command_path: str = "cgi-bin/luci/{command}"

    @override
    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            try:
                async with self._new_client() as client:
                    resp = await client.post(
                        self.base_url + "cgi-bin/luci",
                        data={"luci_username": self.username, "luci_password": pwd},
                        follow_redirects=True,
                    )
                    resp.raise_for_status()
            except (httpx.ConnectError, httpx.TimeoutException):
                raise FailedConnectionError("Failed to connect or timeout occurred")
            except httpx.HTTPStatusError:
                continue
            else:
                if resp.status_code == 200:
                    self.command_path = f"{resp.url.path[1:]}/{{command}}"
                    self.cookies = resp.request.headers.get("Cookie")
                    self.authed = True
                    self.pwd = pwd
                    break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    async def get_mac_addr(self) -> str:
        resp = await self.get_network_info()
        for iface in resp.ifaces:
            if iface.is_up:
                return iface.macaddr
        return ""

    async def get_api_version(self) -> str:
        resp = await self.summary()
        return resp.version

    async def get_system_info(self) -> SystemInfo:
        resp = await self.send_command(
            method="GET", command="admin/status/overview", params={"status": "1"}
        )
        try:
            resobj = SystemInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_network_info(self) -> NetworkInfo:
        resp = await self.send_command(
            method="GET", command="admin/network/iface_status/lan"
        )
        try:
            resobj = NetworkInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    # async def log(self, *args, **kwargs) -> dict:
    #     # admin/ipollo_main/cgminerapi
    #     # admin/status/syslog
    #     # admin/status/dmesg
    #     return await super().log(*args, **kwargs)

    async def summary(self) -> MinerStatus:
        resp = await self.send_command(
            method="GET", command="admin/ipollo_main/api_getstatus"
        )
        try:
            resobj = MinerStatus.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_miner_conf(self) -> MinerConfig:
        resp = await self.send_command(method="GET", command="admin/ipollo_main/normal")
        html = resp.get("text")
        if not isinstance(html, str):
            raise APIInvalidResponse(
                reason="iPollo configuration page returned no HTML"
            )

        parser = _MinerConfigHTMLParser()
        parser.feed(html)

        model_values: dict[str, str] = {}
        for field_name, field in MinerConfig.model_fields.items():
            alias = field.serialization_alias
            if isinstance(alias, str) and alias in parser.values:
                model_values[field_name] = parser.values[alias]
        if not model_values:
            raise APIInvalidResponse(
                reason="iPollo configuration page contained no cgminer controls"
            )

        try:
            config = MinerConfig.model_validate(model_values)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse(reason=str(e)) from e
        return config

    # async def set_miner_conf(self, conf: APIObject) -> APIObject:
    #     # admin/ipollo_main/normal
    #     return await super().set_miner_conf(conf)

    async def pools(self) -> list[MinerPool]:
        resp = await self.send_command(
            method="GET", command="admin/ipollo_main/api_getstatus"
        )
        try:
            resobj = MinerStatus.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.pool

    async def _parse_pool_conf(self, resp: dict) -> MinerConfigPool:
        html = resp.get("text")
        if not isinstance(html, str):
            raise APIInvalidResponse(
                reason="iPollo pool configuration page returned no HTML"
            )

        parser = _MinerConfigHTMLParser()
        parser.feed(html)

        model_values: dict[str, str] = {}
        for field_name, field in MinerConfigPool.model_fields.items():
            alias = field.serialization_alias
            if isinstance(alias, str) and alias in parser.values:
                model_values[field_name] = parser.values[alias]
        if not model_values:
            raise APIInvalidResponse(
                reason="iPollo pool configuration page contained no cgminer controls"
            )

        try:
            config = MinerConfigPool.model_validate(model_values)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        return config

    async def get_pool_conf(self) -> PoolConfig:
        resp = await self.send_command(method="GET", command="admin/ipollo_main/pool")
        config = await self._parse_pool_conf(resp)
        return PoolConfig(config.active_pools())

    @override
    async def start(self) -> APIObject:
        await self.send_command(
            method="POST", command="admin/ipollo_main/cgminerstatus/ctrl/start"
        )
        return ActionResultModel(success=True, msg="OK").model_dump()

    @override
    async def stop(self) -> APIObject:
        await self.send_command(
            method="POST", command="admin/ipollo_main/cgminerstatus/ctrl/stop"
        )
        return ActionResultModel(success=True, msg="OK").model_dump()

    @override
    async def restart(self) -> APIObject:
        await self.send_command(
            method="POST", command="admin/ipollo_main/cgminerstatus/ctrl/restart"
        )
        return ActionResultModel(success=True, msg="OK").model_dump()

    @override
    async def reboot(self) -> APIObject:
        await self.send_command(
            method="POST", command="admin/system/reboot", params={"reboot": "1"}
        )
        return ActionResultModel(success=True, msg="OK").model_dump()

    @override
    async def update_passwd(self, old_passwd: str, new_passwd: str) -> APIObject:
        pw_conf = MinerPasswdConfig(new_passwd=new_passwd, confirm_passwd=new_passwd)
        await self.send_command(
            method="POST",
            command="admin/ipollo_main/passwdchange",
            data=pw_conf.model_dump(by_alias=True),
        )
        return ActionResultModel(success=True, msg="OK").model_dump()

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        resp = await self.send_command(method="GET", command="admin/ipollo_main/pool")
        config = await self._parse_pool_conf(resp)
        pool_conf = [pool.model_dump(by_alias=True) for pool in config.active_pools()]

        coin = config.select_coin
        for i in range(3):
            if not any(pool_conf[i].values()) and not any(
                (urls[i], users[i], passwds[i])
            ):
                continue

            idx = i + 1
            setattr(config, f"{coin}_pool{idx}_url", urls[i])
            setattr(config, f"{coin}_pool{idx}_user", users[i])
            setattr(config, f"{coin}_pool{idx}_pw", passwds[i])

        await self.send_command(
            method="POST",
            command="admin/ipollo_main/pool",
            data=config.model_dump(mode="json", by_alias=True),
        )
        return ActionResultModel(success=True, msg="OK").model_dump()
