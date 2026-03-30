import json
import logging
import re
from string import Template

import requests
from pydantic import BaseModel, Field, TypeAdapter, ValidationError
from requests.auth import HTTPDigestAuth

from mod.apiv2 import settings
from mod.apiv2.base import BaseHTTPClient
from mod.apiv2.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)

logger = logging.getLogger(__name__)


class APIResponse(BaseModel):
    code: int
    msg: str = ""
    data: str = ""


class SystemInfo(BaseModel):
    minertype: str
    nettype: str
    netdevice: str
    macaddr: str
    hostname: str
    ipaddress: str
    netmask: str
    gateway: str
    dnsservers: str
    curtime: str
    uptime: str
    loadaverage: str
    mem_total: str
    mem_used: str
    mem_free: str
    mem_buffers: str
    mem_cached: str
    system_mode: str
    bb_hwv: str
    system_kernel_version: str
    system_filesystem_version: str
    cgminer_version: str


class NetInfo(BaseModel):
    nettype: str
    netdevice: str
    macaddr: str
    ipaddress: str
    netmask: str
    conf_nettype: str
    conf_hostname: str
    conf_ipaddress: str
    conf_netmask: str
    conf_gateway: str
    conf_dnsservers: str


class NetInfoV1(BaseModel):
    bb_nettype: str
    bb_netdevice: str
    bb_macaddr: str
    bb_ipaddress: str
    bb_netmask: str
    bb_conf_nettype: str
    bb_conf_hostname: str
    bb_conf_ipaddress: str
    bb_conf_netmask: str
    bb_conf_gateway: str
    bb_conf_dnsservers: str


class MinerConfPool(BaseModel):
    url: str = ""
    user: str = ""
    passwd: str = Field("", alias="pass")


class MinerConfig(BaseModel):
    fan_ctrl: bool = Field(False, alias="fan-ctrl")
    fan_pwm_front: str | None = Field(None, alias="fan-pwn-front")
    fan_pwm_back: str | None = Field(None, alias="fan-pwn-back")
    use_vil: bool = Field(alias="use-vil")
    freq: str
    sram_voltage: str = Field(alias="sram-voltage")
    coin_type: str = Field(alias="coin-type")
    pools: list[MinerConfPool]


class DebugConfig(BaseModel):
    bb_debug_enable: bool
    tm: str
    bb_pll_switch_time: int
    bb_pll_switch_step: int
    bb_chain0_active_chipnum: int
    bb_chain1_active_chipnum: int
    bb_chain2_active_chipnum: int
    bb_chain3_active_chipnum: int
    bb_chain4_active_chipnum: int
    bb_chain5_active_chipnum: int
    bb_chain6_active_chipnum: int
    bb_chain7_active_chipnum: int
    bb_chain0_freq: int
    bb_chain1_freq: int
    bb_chain2_freq: int
    bb_chain3_freq: int
    bb_chain4_freq: int
    bb_chain5_freq: int
    bb_chain6_freq: int
    bb_chain7_freq: int
    bb_startup_voltage: int
    bb_target_voltage: int


class MinerConfigV1(BaseModel):
    miner: MinerConfig
    debug: DebugConfig = Field(alias="debug")
    keepower: str
    runmode: str
    voltage: str


class Pool(BaseModel):
    index: int
    url: str
    user: str
    status: str
    diff: float
    getworks: str
    priority: int
    accepted: str
    nonce: str
    diffa: str
    diffr: str
    diffs: str
    rejected: str
    discarded: str
    stale: str
    lsdiff: str
    lstime: str


class Chain(BaseModel):
    index: int
    chain_acn: int
    temp: int
    hw: int
    chain_rate: float
    chain_acs: str
    freq: str


class FanInfo(BaseModel):
    fan1: str
    fan2: str
    fan3: str
    fan4: str


class PoolTotal(BaseModel):
    t_getworks: str
    t_accepted: str
    t_nonce: str
    t_diffa: str
    t_diffr: str
    t_diffs: str
    t_rejected: str
    t_discarded: str
    t_stale: str


class HwTotal(BaseModel):
    h_hw: int
    h_diff1_ratio: float
    h_diffa_ratio: float


class PoolStats(BaseModel):
    total: PoolTotal
    hw: HwTotal
    pool_dtls: list[Pool]


class Summary(BaseModel):
    elapsed: str
    ghs5s: str
    ghsav: str
    localwork: str
    utility: float
    wu: str
    bestshare: int


class MinerStatus(BaseModel):
    elapsed: str
    ghs5s: str
    ghsav: str
    localwork: str
    utility: float
    wu: str
    bestshare: int
    pools: PoolStats
    chains: list[Chain]
    fan: FanInfo


class VolcminerHTTPClient(BaseHTTPClient):
    def __init__(self, ip: str, port: int = 80, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)
        self.username: str = "root"
        if alt_pwd:
            settings.set_auth_alt("volcminer", alt_pwd)
        self.passwds = settings.get_auth_list("volcminer")

        self.command_path = Template("cgi-bin/${command}.cgi")

    def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            try:
                self.session.auth = HTTPDigestAuth(self.username, pwd)
                resp = self.session.get(
                    self.base_url, timeout=settings.get("http_request_timeout", 5.0)
                )
                resp.raise_for_status()
            except (
                requests.HTTPError,
                requests.ConnectionError,
                requests.Timeout,
            ) as ex:
                if isinstance(ex, requests.ConnectionError) or isinstance(
                    ex, requests.Timeout
                ):
                    raise FailedConnectionError("Failed to connect or timeout occurred")
                elif isinstance(ex, requests.HTTPError):
                    continue
            else:
                if resp.status_code == 200:
                    self.authed = True
                    self.pwd = pwd
                    self.digest = self.session.auth
                    break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    def get_hostname(self) -> str:
        resp = self.get_network_info()
        return resp["conf_hostname"]

    def get_mac_addr(self) -> str:
        resp = self.get_network_info()
        return resp["macaddr"]

    def get_api_version(self) -> str:
        return super().get_api_version()

    def get_system_info(self) -> dict:
        resp = self.send_command("GET", command="get_system_info")
        try:
            resobj = SystemInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    def get_network_info(self) -> dict:
        resp = self.send_command("GET", command="get_network_info")
        try:
            resobj = NetInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    def get_network_infoV1(self) -> dict:
        """Volcminer: get network info from 'get_network_infoV1' endpoint"""
        resp = self.send_command(method="GET", command="get_network_infoV1")
        cleaned = re.sub(r"\s{1,}", "", resp["text"])
        try:
            data = re.search(r'"data":"\{(.*?)\}"', cleaned).group(1)
        except AttributeError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        net_info = json.loads("{" + data + "}")
        try:
            resobj = NetInfoV1.model_validate(obj=net_info)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    def get_miner_conf(self) -> dict:
        resp = self.send_command("GET", command="get_miner_conf")
        try:
            resobj = MinerConfig.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(exclude_none=True)

    def get_miner_confV1(self) -> dict:
        """Volcminer: get miner config from 'get_miner_confV1' endpoint"""
        resp = self.send_command(method="GET", command="get_miner_confV1")
        cleaned = re.sub(r"\s{1,}", "", resp["text"])
        try:
            parts = re.search(
                r'"cfgs":"\[(.*?)\]",(.*?),"debug":"\{(.*?)\}",(.*?)\}', cleaned
            ).groups()
        except AttributeError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        cfgs = parts[0]
        keep_power = parts[1]
        debug = parts[2]
        extra = parts[3]
        try:
            miner_conf = json.loads(
                '{"miner":'
                + cfgs
                + ","
                + keep_power
                + ',"debug":{'
                + debug
                + "},"
                + extra
                + "}"
            )
        except json.JSONDecodeError:
            raise APIError("Failed to decode JSON from API response.")
        try:
            resobj = MinerConfigV1.model_validate(obj=miner_conf, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(exclude_none=True, by_alias=True)

    def set_miner_conf(self, conf: dict) -> dict:
        return self.send_command("POST", command="set_miner_conf", data=conf)

    def log(self, *args, **kwargs) -> dict:
        return super().log(*args, **kwargs)

    def summary(self) -> dict:
        resp = self.send_command("GET", command="get_miner_statusV1")
        cleaned = re.sub(r"\s{1,}", "", resp["text"])
        try:
            data = re.search(r'"data":"\{(.*?)\}"', cleaned).group(1)
            parts = re.search(
                r'(.*?),"pool_dtls":"\[(.*?)\]"\},"chains":"\[(.*?)\]",(.*?)$', data
            ).groups()
        except AttributeError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        status = parts[0]
        pools = parts[1]
        chains = parts[2]
        fans = parts[3]
        try:
            miner_status = json.loads(
                "{"
                + status
                + ',"pool_dtls":['
                + pools
                + "]},"
                + '"chains":['
                + chains
                + "],"
                + fans
                + "}"
            )
        except json.JSONDecodeError:
            raise APIError("Failed to decode JSON from API response.")
        try:
            resobj = MinerStatus.model_validate(obj=miner_status)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    def pools(self) -> list[dict]:
        resp = self.summary()
        ta = TypeAdapter(list[Pool])
        pools = ta.validate_python(resp["pools"]["pool_dtls"])
        return ta.dump_python(pools)

    def get_pool_conf(self) -> list[dict]:
        resp = self.get_miner_conf()
        ta = TypeAdapter(list[MinerConfPool])
        pools = ta.validate_python(resp["pools"], by_name=True)
        return ta.dump_python(pools, by_alias=True)

    def get_miner_status(self) -> dict:
        return super().get_miner_status()

    def get_blink_status(self) -> dict:
        return super().get_blink_status()

    def blink(self, enabled: bool, *args, **kwargs) -> dict:
        data = {"_bb_type": "rgOn" if enabled else "rgOff"}
        return self.send_command("POST", command="post_led_onoff", data=data)

    def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        resp = self.get_miner_confV1()
        conf = MinerConfigV1.model_construct(**resp)
        miner = MinerConfig(**resp["miner"])
        ta = TypeAdapter(list[MinerConfPool])
        pools = ta.validate_python(miner.pools, by_name=True)
        pool_conf: list[dict[str, str]] = ta.dump_python(pools, by_alias=True)

        data = {}
        for i in range(0, len(urls)):
            if (
                not any(pool_conf[i].values())
                and not len(urls[i])
                and not len(users[i])
            ):
                continue
            data[f"_bb_pool{i + 1}url"] = urls[i]
            data[f"_bb_pool{i + 1}user"] = users[i]
            data[f"_bb_pool{i + 1}pw"] = passwds[i] if len(passwds[i]) else "x"

        data["_bb_nobeeper"] = ""
        data["_bb_notempoverctrl"] = "false"
        if miner.fan_ctrl:
            data["_bb_fan_customize_switch"] = "true"
            data["_bb_fan_customize_value_front"] = miner.fan_pwm_front
            data["_bb_fan_customize_value_back"] = miner.fan_pwm_back
        else:
            data["_bb_fan_customize_switch"] = "false"
            data["_bb_fan_customize_value_front"] = ""
            data["_bb_fan_customize_value_back"] = ""

        data["_bb_freq"] = miner.freq
        data["_bb_coin_type"] = miner.coin_type
        data["_bb_runmode"] = conf.runmode
        data["_bb_voltage_customize_value"] = conf.voltage
        data["_bb_ema"] = miner.sram_voltage
        data["_bb_debug"] = "false"

        return self.set_miner_conf(conf=data)
