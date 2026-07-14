import json
import logging
from string import Template
from typing import Any

import httpx
from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from mod.ipr_asic import settings
from mod.ipr_asic.data import BlinkStatus, MinerConfPool
from mod.ipr_asic.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)
from mod.ipr_asic.protocol import BaseHTTPClient
from mod.ipr_asic.rpc.cgminer import Status, Version

logger = logging.getLogger(__name__)


class NetworkInfo(BaseModel):
    command: str
    protocol: str
    ip: str
    mask: str
    gateway: str
    dns: str
    hostname: str


class IPReport(BaseModel):
    command: str
    serial: str = Field(alias="SerialNo")
    ip: str
    mac: str
    model: str
    gateway: str | None = None
    mask: str | None = None
    model_version: str | None = Field(None, alias="ModelVersion")
    version: str
    hostname: str
    orgid: str | None = None
    pubkey: str = Field(alias="pubKey")
    tpm_pubkey: str = Field(alias="tpmPubKey")
    cb_serial: str = Field(alias="CBSerialNo")
    chassis_serial: str = Field(alias="ChassisSerialNo")
    hb_serials: list[str] = Field(default_factory=list[str], alias="HBSerialNo")
    internal_type: str | None = Field(None, alias="InternalType")


class Pool(BaseModel):
    pool: int = Field(alias="POOL")
    url: str = Field(alias="URL")
    status: str = Field(alias="Status")
    priority: int = Field(alias="Priority")
    quota: int = Field(alias="Quota")
    long_poll: str = Field(alias="Long Poll")
    getworks: int = Field(alias="Getworks")
    accepted: int = Field(alias="Accepted")
    rejected: int = Field(alias="Rejected")
    works: int = Field(alias="Works")
    discarded: int = Field(alias="Discarded")
    stale: int = Field(alias="Stale")
    get_failures: int = Field(alias="Get Failures")
    remote_failures: int = Field(alias="Remote Failures")
    user: str = Field(alias="User")
    passwd: str = Field(validation_alias="Pass")
    last_share_time: int = Field(alias="Last Share Time")
    diff1_shares: int = Field(alias="Diff1 Shares")
    proxy_type: str = Field(alias="Proxy Type")
    proxy: str = Field(alias="Proxy")
    diffa: int = Field(alias="Difficulty Accepted")
    diffr: int = Field(alias="Difficulty Rejected")
    diffs: int = Field(alias="Difficulty Stale")
    last_share_difficulty: int = Field(alias="Last Share Difficulty")
    work_difficulty: int = Field(alias="Work Difficulty")
    has_stratum: bool = Field(alias="Has Stratum")
    stratum_active: bool = Field(alias="Stratum Active")
    stratum_url: str = Field(alias="Stratum URL")
    stratum_diff: int = Field(alias="Stratum Difficulty")
    has_vmask: bool = Field(alias="Has Vmask")
    has_gbt: bool = Field(alias="Has GBT")
    best_share: int = Field(alias="Best Share")
    pool_rejected_: float = Field(alias="Pool Rejected%")
    pool_stale_: float = Field(alias="Pool Stale%")
    bad_work: int = Field(alias="Bad Work")
    current_block_height: int = Field(alias="Current Block Height")
    current_block_version: int = Field(alias="Current Block Version")
    protocol: str = Field(alias="Protocol")


class Summary(BaseModel):
    elapsed: int = Field(alias="Elapsed")
    mhs_av: float = Field(alias="MHS av")
    mhs_5s: float = Field(alias="MHS 5s")
    mhs_1m: float = Field(alias="MHS 1m")
    mhs_5m: float = Field(alias="MHS 5m")
    mhs_15m: float = Field(alias="MHS 15m")
    mhs_24h: float = Field(alias="MHS 24h")
    gmhs_av: float = Field(alias="GMHS av")
    gmhs_5s: float = Field(alias="GMHS 5s")
    gmhs_1m: float = Field(alias="GMHS 1m")
    gmhs_5m: float = Field(alias="GMHS 5m")
    gmhs_15m: float = Field(alias="GMHS 15m")
    gmhs_24h: float = Field(alias="GMHS 24h")
    pool_mhs_30m: int = Field(alias="Pool MHS 30m")
    pool_mhs_60m: int = Field(alias="Pool MHS 60m")
    pool_mhs_24h: int = Field(alias="Pool MHS 24h")
    getworks: int = Field(alias="Getworks")
    accepted: int = Field(alias="Accepted")
    rejected: int = Field(alias="Rejected")
    hardware_errors: int = Field(alias="Hardware Errors")
    utility: float = Field(alias="Utility")
    discarded: int = Field(alias="Discarded")
    stale: int = Field(alias="Stale")
    get_failures: int = Field(alias="Get Failures")
    local_work: int = Field(alias="Local Work")
    remote_failures: int = Field(alias="Remote Failures")
    total_mh: int = Field(alias="Total MH")
    total_gmh: int = Field(alias="Total GMH")
    work_utility: int = Field(alias="Work Utility")
    difficulty_accepted: int = Field(alias="Difficulty Accepted")
    difficulty_rejected: int = Field(alias="Difficulty Rejected")
    difficulty_stale: int = Field(alias="Difficulty Stale")
    best_share: int = Field(alias="Best Share")
    device_hardware_: int = Field(alias="Device Hardware%")
    device_rejected_: int = Field(alias="Device Rejected%")
    pool_rejected_: float = Field(alias="Pool Rejected%")
    pool_stale_: int = Field(alias="Pool Stale%")
    last_getwork: int = Field(alias="Last getwork")
    wattage: int = Field(alias="Wattage")
    ths_throttle: float = Field(alias="ThsThrottle")
    jths_1m: float = Field(alias="JTHS 1m")


class Mode(BaseModel):
    command: str
    mode: str | None = Field(None, pattern=r"normal|eco|turbo|custom")
    sleep: str | None = Field(None, pattern=r"on|off")
    tune: str | None = Field(None, pattern=r"ths|power")
    ths: float | None = Field(None)
    power: int | None = Field(None, ge=0, le=10000)
    fans_in_standby: str | None = Field(
        None, pattern=r"on|off", serialization_alias="fansInStandby"
    )
    coolant_default_action: str | None = Field(
        None, pattern=r"on|off", serialization_alias="coolantDefaultAction"
    )
    retune_time: int | None = Field(
        None, ge=30, le=2880, serialization_alias="retuneTime"
    )
    optimize_eco: str | None = Field(
        None, pattern=r"on|off", serialization_alias="optimizeEco"
    )
    mining_if_net_down: str | None = Field(
        None, pattern=r"on|off", serialization_alias="miningIfNetDown"
    )
    persist_standby: str | None = Field(
        None, pattern=r"on|off", serialization_alias="persistStandby"
    )
    leak_detected: str | None = Field(
        None, pattern=r"on|off", serialization_alias="leakDetected"
    )


class ModeResponse(BaseModel):
    mode: str | None = Field(None, alias="Mode")
    sleep: str | None = Field(None, alias="Sleep")
    tune: str | None = Field(None, alias="Tune")
    ths: float | None = Field(None, alias="Ths")
    power: int | None = Field(None, alias="Power")
    fans_in_standby: str | None = Field(None, alias="FansInStandby")
    coolant_default_action: str | None = Field(None, alias="coolantDefaultAction")
    retune_time: int | None = Field(None, alias="reTuneTime")
    retune_count: int | None = Field(None, alias="reTuneCount")
    optimize_eco: str | None = Field(None, alias="optimizeEco")
    mining_if_net_down: str | None = Field(None, alias="miningIfNetDown")
    persist_standby: str | None = Field(None, alias="persistStandby")
    leak_detected: str | None = Field(None, alias="leakDetected")


class LED(BaseModel):
    command: str
    code: int
    led1: int | None = None
    led2: int | None = None
    msg: str | None = None


class LEDResponse(BaseModel):
    code: int = Field(
        validation_alias="Code",
    )
    led1: int = Field(validation_alias="LED1")
    led2: int = Field(validation_alias="LED2")
    msg: str = Field(validation_alias="Msg")
    standby_reason: str | None = Field(None, validation_alias="standbyReason")
    display_msg: str | None = Field(None, validation_alias="DisplayMsg")


class Token(BaseModel):
    name: str = Field(alias="Name")
    when: int = Field(alias="When")
    token: str = Field(alias="Token")


class WhitelistPools(BaseModel):
    accepted_pools_urls: list[str] = Field(
        default_factory=list[str], validation_alias="acceptedPoolUrls"
    )


class UpdatePoolsResponse(BaseModel):
    msg: str


class Response(BaseModel):
    id: int
    status: list[Status] = Field(alias="STATUS")
    version: list[Version] | None = Field(None, alias="VERSION")
    summary: list[Summary] | None = Field(None, alias="SUMMARY")
    stats: list[dict[str, Any]] | None = Field(None, alias="STATS")
    devs: list[dict[str, Any]] | None = Field(None, alias="DEVS")
    dev_details: list[dict[str, Any]] | None = Field(None, alias="DEVDETAILS")
    pools: list[Pool] | None = Field(None, alias="POOLS")
    network: list[NetworkInfo] | None = Field(None, alias="Network")
    ip_report: list[IPReport] | None = Field(None, alias="IPReport")
    led: list[LEDResponse] | None = Field(None, alias="LED")
    mode: list[ModeResponse] | None = Field(None, alias="Mode")
    whitelist_pools: list[WhitelistPools] | None = Field(None, alias="whitelistPools")
    update_pools: list[UpdatePoolsResponse] | None = Field(None, alias="UPDATEPOOLS")
    token: list[Token] | None = Field(None, alias="Token")

    def error(self) -> str | None:
        for status in self.status:
            match status.status:
                case "E" | "F":
                    return f"received API error ({status.code}) {status.msg} - {status.description}"
                case _:
                    return None


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
        self.passwds = settings.get_auth_list("auradine")

        self.command_path = Template("${command}")
        self.token = None

    def _validate_response(self, data: dict) -> Response:
        try:
            resobj = Response.model_validate(obj=data, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            err = resobj.error()
            if err:
                logger.error(f"{self.__repr__()} : {str(APIError(err))}")
                raise APIError("Command failed!")
            return resobj

    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            data = '{"command":"token","user":"%s","password":"%s"}' % (
                self.username,
                pwd,
            )
            try:
                async with self._new_client() as client:
                    resp = await client.post(self.base_url + "token", data=data)
                    resp.raise_for_status()
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
        return resp["hostname"]

    async def get_mac_addr(self) -> str:
        resp = await self.get_system_info()
        return resp["mac"]

    async def get_api_version(self) -> str:
        return await super().get_api_version()

    async def get_system_info(self) -> dict:
        resp = await self.send_command("GET", command="ipreport2")
        valid = self._validate_response(resp)
        if valid.ip_report is None or len(valid.ip_report) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.ip_report[0].model_dump(by_alias=True, exclude_none=True)

    async def get_network_info(self) -> dict:
        resp = await self.send_command("GET", command="network")
        valid = self._validate_response(resp)
        if valid.network is None or len(valid.network) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.network[0].model_dump()

    async def log(self, *args, **kwargs) -> dict:
        return await super().log(*args, **kwargs)

    async def summary(self) -> dict:
        resp = await self.send_command("GET", command="summary")
        valid = self._validate_response(resp)
        if valid.summary is None or len(valid.summary) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.summary[0].model_dump(by_alias=True)

    async def get_miner_conf(self) -> dict:
        resp = await self.send_command("GET", command="mode")
        valid = self._validate_response(resp)
        if valid.mode is None or len(valid.mode) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.mode[0].model_dump(by_alias=True, exclude_none=True)

    async def set_miner_conf(self, conf: dict) -> dict:
        try:
            mode = Mode.model_validate(conf)
            mode.command = "mode"
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

    async def pools(self) -> list[dict]:
        resp = await self.send_command("GET", command="pools")
        valid = self._validate_response(resp)
        if valid.pools is None:
            raise APIInvalidResponse(reason="malformed")
        else:
            ta = TypeAdapter(list[Pool])
            pools = ta.validate_python(valid.pools, by_alias=True)
            return ta.dump_python(pools, by_alias=True, exclude_none=True)

    async def get_pool_conf(self) -> list[dict]:
        pools = await self.pools()
        pool_conf = []
        for pool in pools:
            pool_conf.append(
                MinerConfPool(
                    url=pool["URL"], user=pool["User"], passwd=pool["passwd"]
                ).model_dump(by_alias=True)
            )
        return pool_conf

    async def get_whitelisted_pools(self) -> dict:
        resp = await self.send_command("GET", command="whitelistpools")
        valid = self._validate_response(resp)
        if valid.whitelist_pools is None or len(valid.whitelist_pools) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.whitelist_pools[0].model_dump()

    async def get_miner_status(self) -> dict:
        resp = await self.send_command("GET", command="led")
        valid = self._validate_response(resp)
        if valid.led is None or len(valid.led) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.led[0].model_dump(by_alias=True, exclude_none=True)

    async def get_blink_status(self) -> dict:
        resp = await self.send_command("GET", command="led")
        valid = self._validate_response(resp)
        if valid.led is None or len(valid.led) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            blink = BlinkStatus(
                blink=True
                if valid.led[0].code == 3
                or (valid.led[0].led1 == 4 and valid.led[0].led2 == 4)
                else False
            )
            return blink.model_dump()

    async def blink(
        self,
        enabled: bool,
    ) -> dict:
        led = LED(
            command="led",
            code=3 if enabled else 2,
        )
        resp = await self.send_command(
            "POST", command="led", payload=led.model_dump(exclude_none=True)
        )
        _ = self._validate_response(resp)
        return resp

    async def set_led(self, led1: int, led2: int, msg: str, code: int = 102):
        led = LED(command="led", code=code, led1=led1, led2=led2, msg=msg)
        resp = await self.send_command("POST", command="led", payload=led.model_dump())
        _ = self._validate_response(resp)
        return resp

    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        pool_conf: list[dict[str, str]] = []
        for i in range(0, len(urls)):
            if not len(urls[i]) and not len(users[i]):
                continue
            pool_conf.append(
                MinerConfPool(url=urls[i], user=users[i], passwd=passwds[i]).model_dump(
                    by_alias=True
                )
            )
        pools = {"command": "updatepools", "pools": pool_conf}
        resp = await self.send_command("POST", command="updatepools", payload=pools)
        valid = self._validate_response(resp)
        if valid.update_pools is None or len(valid.update_pools) != 1:
            raise APIInvalidResponse(reason="malformed")
        return resp
