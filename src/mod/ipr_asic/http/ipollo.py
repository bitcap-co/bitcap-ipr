import logging
from html.parser import HTMLParser
from typing import Literal

import httpx
from pydantic import BaseModel, Field, RootModel, TypeAdapter, ValidationError

from mod.ipr_asic import settings
from mod.ipr_asic.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)
from mod.ipr_asic.models import ActionResponse, MinerConfPool
from mod.ipr_asic.protocol import BaseHTTPClient

logger = logging.getLogger(__name__)


class SystemSwap(BaseModel):
    free: int
    total: int


class SystemMemory(BaseModel):
    buffered: int
    total: int
    shared: int
    free: int


class SystemWAN(BaseModel):
    proto: str
    ipaddr: str
    netmask: str
    gwaddr: str
    uptime: int
    ifname: str
    dns: list[str]


class SystemInfo(BaseModel):
    swap: SystemSwap
    conncount: int
    memory: SystemMemory
    uptime: int
    wan: SystemWAN
    localtime: str


class MinerPool(BaseModel):
    pool: int
    user: str
    url: str
    accept: int
    diff: int


class MinerStatus(BaseModel):
    pool: list[MinerPool]
    temp: str | None
    fan: str | None
    accepted: int | None
    rejected: int | None
    unit: str | None
    version: str
    algo: str | None
    mmodel: str | None
    hashrate: float | None


class IPAddresses(BaseModel):
    netmask: str
    addr: str
    prefix: int


class Subdevice(BaseModel):
    type: str
    name: str
    macaddr: str
    is_up: bool
    ifname: str


class Interface(BaseModel):
    ifname: str
    ipaddrs: list[IPAddresses]
    gwaddr: str
    dnsaddrs: list[str]
    proto: str
    id: str
    uptime: int
    subdevices: list[Subdevice]
    is_up: bool
    macaddr: str
    type: str
    name: str


class Interfaces(RootModel[list[Interface]]):
    pass


class MinerConfForm(BaseModel):
    submit: int | None = Field(1, serialization_alias="cbi.submit")
    apply: Literal["Save & Apply"] = Field(
        "Save & Apply", serialization_alias="cbi.apply"
    )


class MinerNetworkConfig(MinerConfForm):
    proto: Literal["dhcp", "static"] = Field(
        "dhcp", serialization_alias="cbid.network.lan.proto"
    )
    ipaddr: str | None = Field(None, serialization_alias="cbid.network.lan.ipaddr")
    netmask: str | None = Field(None, serialization_alias="cbid.network.lan.netmask")
    gateway: str | None = Field(None, serialization_alias="cbid.network.lan.gateway")
    dns: str | None = Field(None, serialization_alias="cbid.network.lan.dns")


class _MinerConfigHTMLParser(HTMLParser):
    """Extract LuCI cgminer configuration values from form controls."""

    field_prefix = "cbid.cgminer.default."

    def __init__(self) -> None:
        super().__init__()
        self.values: dict[str, str] = {}
        self._select_name: str | None = None

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

    def handle_endtag(self, tag: str) -> None:
        if tag == "select":
            self._select_name = None


class MinerConfig(MinerConfForm):
    show_fan: Literal["fan1", "fan2", "fan3", "fan4"] = Field(
        "fan1", serialization_alias="cbid.cgminer.default.show_fan"
    )
    show_temp: Literal["temp1", "temp2", "temp3", "temp4", "temp5", "temp6"] = Field(
        "temp2", serialization_alias="cbid.cgminer.default.show_temp"
    )
    alarm_temp: int = Field(
        90, ge=-55, le=155, serialization_alias="cbid.cgminer.default.asic_alarm_temp"
    )
    fan_min: int = Field(
        20, ge=0, le=100, serialization_alias="cbid.cgminer.default.fan_min"
    )
    fan_max: int = Field(
        100, ge=0, le=100, serialization_alias="cbid.cgminer.default.fan_max"
    )
    default_pwm: int = Field(
        30, ge=0, le=100, serialization_alias="cbid.cgminer.default.pwm_default"
    )
    fan_ctrl: int = Field(
        1, ge=0, le=1, serialization_alias="cbid.cgminer.default.fan_ctrl"
    )
    pre_boot_time: int = Field(
        3, ge=0, le=10, serialization_alias="cbid.cgminer.default.pre_boot_time"
    )
    pre_boot_fan: int = Field(
        100, ge=0, le=100, serialization_alias="cbid.cgminer.default.pre_boot_fan"
    )


class MinerConfigPool(MinerConfForm):
    select_coin: Literal["mwc", "grin"] = Field(
        "mwc", serialization_alias="cbid.cgminer.default.select_coin"
    )
    mwc_pool1_url: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool1url"
    )
    mwc_pool1_user: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool1user"
    )
    mwc_pool1_pw: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool1pw"
    )
    mwc_pool2_url: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool2url"
    )
    mwc_pool2_user: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool2user"
    )
    mwc_pool2_pw: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool2pw"
    )
    mwc_pool3_url: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool3url"
    )
    mwc_pool3_user: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool3user"
    )
    mwc_pool3_pw: str = Field(
        "", serialization_alias="cbid.cgminer.default.mwc_pool3pw"
    )
    grin_pool1_url: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool1url"
    )
    grin_pool1_user: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool1user"
    )
    grin_pool1_pw: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool1pw"
    )
    grin_pool2_url: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool2url"
    )
    grin_pool2_user: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool2user"
    )
    grin_pool2_pw: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool2pw"
    )
    grin_pool3_url: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool3url"
    )
    grin_pool3_user: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool3user"
    )
    grin_pool3_pw: str = Field(
        "", serialization_alias="cbid.cgminer.default.grin_pool3pw"
    )
    api_allow: str = Field("", serialization_alias="cbid.cgminer.default.api_allow")
    more_options: str = Field(
        "", serialization_alias="cbid.cgminer.default.more_options"
    )
    ntp_enable: str = Field("", serialization_alias="cbid.cgminer.default.ntp_enable")

    def active_pools(self) -> list[MinerConfPool]:
        coin = self.select_coin
        return [
            MinerConfPool.model_validate(
                {
                    "url": getattr(self, f"{coin}_pool{index}_url"),
                    "user": getattr(self, f"{coin}_pool{index}_user"),
                    "pass": getattr(self, f"{coin}_pool{index}_pw"),
                }
            )
            for index in range(1, 4)
        ]


class MinerConfigPasswd(MinerConfForm):
    new_passwd: str = Field("", serialization_alias="cbid.system._pass.pw1")
    confirm_passwd: str = Field("", serialization_alias="cbid.system._pass.pw2")


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
        self.passwds = settings.get_auth_list("ipollo")

        self.command_path = "cgi-bin/luci/{command}"

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

    async def get_hostname(self) -> str:
        return await super().get_hostname()

    async def get_mac_addr(self) -> str:
        return await super().get_mac_addr()

    async def get_api_version(self) -> str:
        return await super().get_api_version()

    async def get_system_info(self) -> dict:
        resp = await self.send_command(
            method="GET", command="admin/status/overview", params={"status": "1"}
        )
        try:
            resobj = SystemInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def get_network_info(self) -> dict:
        resp = await self.send_command(
            method="GET", command="admin/network/iface_status/lan"
        )
        try:
            resobj = Interfaces.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.model_dump()[0]

    async def log(self, *args, **kwargs) -> dict:
        # admin/ipollo_main/cgminerapi
        # admin/status/syslog
        # admin/status/dmesg
        return await super().log(*args, **kwargs)

    async def summary(self) -> dict:
        resp = await self.send_command(
            method="GET", command="admin/ipollo_main/api_getstatus"
        )
        try:
            resobj = MinerStatus.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    async def get_miner_conf(self) -> dict:
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
        return config.model_dump()

    async def set_miner_conf(self, *args, **kwargs) -> dict:
        # admin/ipollo_main/normal
        return await super().set_miner_conf(*args, **kwargs)

    async def pools(self) -> list[dict]:
        resp = await self.send_command(
            method="GET", command="admin/ipollo_main/api_getstatus"
        )
        try:
            resobj = MinerStatus.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            ta = TypeAdapter(list[MinerPool])
            return ta.dump_python(resobj.pool)

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

    async def get_pool_conf(self) -> list[dict]:
        resp = await self.send_command(method="GET", command="admin/ipollo_main/pool")
        config = await self._parse_pool_conf(resp)
        return [pool.model_dump(by_alias=True) for pool in config.active_pools()]

    async def get_miner_status(self) -> dict:
        return await super().get_miner_status()

    async def get_blink_status(self) -> dict:
        return await super().get_blink_status()

    async def blink(self, enabled: bool, *args, **kwargs) -> dict:
        return await super().blink(enabled, *args, **kwargs)

    async def set_miner_mode(self, *args, **kwargs) -> dict:
        return await super().set_miner_mode(*args, **kwargs)

    async def start(self) -> dict:
        await self.send_command(
            method="POST", command="admin/ipollo_main/cgminerstatus/ctrl/start"
        )
        return ActionResponse(success=True, msg="OK").model_dump()

    async def stop(self) -> dict:
        await self.send_command(
            method="POST", command="admin/ipollo_main/cgminerstatus/ctrl/stop"
        )
        return ActionResponse(success=True, msg="OK").model_dump()

    async def restart(self) -> dict:
        await self.send_command(
            method="POST", command="admin/ipollo_main/cgminerstatus/ctrl/restart"
        )
        return ActionResponse(success=True, msg="OK").model_dump()

    async def reboot(self) -> dict:
        await self.send_command(
            method="POST", command="admin/system/reboot", params={"reboot": "1"}
        )
        return ActionResponse(success=True, msg="OK").model_dump()

    async def update_passwd(self, old_passwd: str, new_passwd: str) -> dict:
        pw_conf = MinerConfigPasswd(new_passwd=new_passwd, confirm_passwd=new_passwd)
        await self.send_command(
            method="POST",
            command="admin/ipollo_main/passwdchange",
            data=pw_conf.model_dump(by_alias=True),
        )
        return ActionResponse(success=True, msg="OK").model_dump()

    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
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
        return ActionResponse(success=True, msg="OK").model_dump()
