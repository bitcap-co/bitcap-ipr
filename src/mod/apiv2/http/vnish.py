import logging
from string import Template
from typing import Annotated, Literal

import requests
from pydantic import BaseModel, Field, RootModel, TypeAdapter, ValidationError

from .. import settings
from ..base.http import BaseHTTPClient
from ..errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)

logger = logging.getLogger(__name__)


class VnishError(BaseModel):
    err: str

    def as_str(self) -> str:
        return self.err.replace('[]"', "")


# info
class SystemInfo(BaseModel):
    os: str
    miner_name: str
    file_system_version: str
    network_status: NetworkInfo
    uptime: str


class NetworkInfo(BaseModel):
    mac: str
    dhcp: bool
    ip: str
    netmask: str
    gateway: str
    dns: list[str] = Field(default_factory=list)
    hostname: str


class Info(BaseModel):
    miner: str
    model: str
    fw_name: str
    fw_version: str
    build_uuid: str
    build_name: str
    platform: str
    install_type: str
    build_time: str
    algorithm: str
    hr_measure: str
    system: SystemInfo
    serial: str


# factory-info
class FactoryInfoChain(BaseModel):
    id: int
    board_model: str
    serial: str
    chip_bin: int
    freq: int
    volt: int
    hashrate: float


class FactoryInfoReply(BaseModel):
    hr_stock: float
    has_pics: bool
    psu_model: str
    psu_serial: str
    chains: list[FactoryInfoChain]


# status
class MinerStatus(BaseModel):
    miner_state: str
    miner_state_time: int
    description: str | None = None
    failure_code: int | None = None
    find_miner: bool
    restart_required: bool
    reboot_required: bool
    unlocked: bool
    unlock_timeout: int | None = None


# summary
class MinerStatusSummary(BaseModel):
    miner_state: str
    miner_state_time: int
    description: str | None = None
    failure_code: int | None = None


class TempRange(BaseModel):
    min: int
    max: int


class PoolStats(BaseModel):
    id: int
    url: str
    pool_type: str
    user: str
    status: str
    asic_boost: bool
    diff: str
    accepted: int
    rejected: int
    stale: int
    ls_diff: float
    ls_time: str
    diffa: float
    ping: int


class Fan(BaseModel):
    id: int
    rpm: int
    status: Literal["ok", "lost"]
    max_rpm: int


class CoolingMode(BaseModel):
    name: Literal["manual", "immersion", "auto"]


class CoolingSettingsSummary(BaseModel):
    mode: CoolingMode


class Cooling(BaseModel):
    fan_num: int
    fan_duty: int
    fans: list[Fan]
    settings: CoolingSettingsSummary


class ChainStatus(BaseModel):
    state: Literal[
        "initializing",
        "mining",
        "stopped",
        "failure",
        "disconnected",
        "disabled",
        "unknown",
    ]
    description: str | None = None


class ChipStatuses(BaseModel):
    red: int
    orange: int
    grey: int


class ChainSummary(BaseModel):
    id: int
    frequency: float
    voltage: int
    power_consumption: int
    hashrate_ideal: float
    hashrate_rt: float
    hashrate_percentage: float
    hr_error: float
    hw_errors: int
    pcb_temp: TempRange
    chip_temp: TempRange
    chip_statuses: ChipStatuses
    status: ChainStatus
    inlet_water_temp: int | None = None
    outlet_water_temp: int | None = None


class PSUTemps(BaseModel):
    pfc_temp: int | None = None
    llc1_temp: int | None = None
    llc2_temp: int | None = None


class PSUInfo(BaseModel):
    psu_power_metering: bool | None = None
    temps: PSUTemps | None = None


class MinerSummary(BaseModel):
    miner_status: MinerStatusSummary
    miner_type: str
    hr_stock: float
    hr_realtime: float
    hr_nominal: float
    hr_average: float
    pcb_temp: TempRange
    chip_temp: TempRange
    power_consumption: int
    power_efficiency: float
    hw_errors_percent: float
    hr_error: float
    hw_errors: int
    devfee_percent: float
    devfee: float
    pools: list[PoolStats]
    cooling: Cooling
    chains: list[ChainSummary]
    found_blocks: int
    best_share: int
    psu: PSUInfo | None = None


class Summary(BaseModel):
    miner: MinerSummary


# perf-summary
class PresetSwitcher(BaseModel):
    enabled: bool | None = None
    top_preset: str | None = None
    decrease_temp: Annotated[int, Field(ge=25, le=90)] | None = None
    rise_temp: Annotated[int, Field(le=85)] | None = None
    check_time: Annotated[int, Field(ge=60, le=600)] | None = None
    autochange_top_preset: bool | None = None
    ignore_fan_speed: bool | None = None
    min_preset: str | None = None
    power_delta: Annotated[int, Field(ge=0, le=50)] | None = None


class Globals(BaseModel):
    freq: Annotated[int, Field(ge=0)] | None = None
    volt: Annotated[int, Field(ge=0)] | None = None


class CurrentPreset(BaseModel):
    name: str
    pretty: str
    status: Literal["untuned", "tuned"]
    globals: Globals | None = None
    modded_psu_required: bool


class PerfSummary(BaseModel):
    current_preset: CurrentPreset | None = None
    preset_switcher: PresetSwitcher


# presets
class AutotuneChain(BaseModel):
    chips: list[int]
    freq: int
    serial: str | None = None


class TuneSettings(BaseModel):
    chains: list[AutotuneChain]
    freq: int
    hashrate: int
    modified: bool
    volt: int


class Preset(BaseModel):
    name: str
    pretty: str
    status: Literal["untuned", "tuned"]
    modded_psu_required: bool
    tune_settings: TuneSettings | None = None


class Presets(RootModel[list[Preset]]):
    pass


# settings
class CoolingModeSettings(BaseModel):
    name: Literal["auto", "manual", "immers"]
    param: Annotated[int, Field(ge=0)] | None = None


class CoolingSettings(BaseModel):
    fan_min_duty: Annotated[int, Field(ge=0, le=100)] | None = None
    fan_max_duty: Annotated[int, Field(ge=0, le=100)] | None = None
    fan_min_count: Annotated[int, Field(ge=0)] | None = None
    mode: CoolingModeSettings | None = None


class AdvancedSettings(BaseModel):
    asic_boost: bool | None = None
    restart_hashrate: Annotated[int, Field(ge=0, le=100)] | None = None
    restart_temp: Annotated[int, Field(ge=0)] | None = None
    disable_restart_unbalanced: bool | None = None
    disable_chain_break_protection: bool | None = None
    max_restart_attempts: Annotated[int, Field(ge=0)] | None = None
    bitmain_disable_volt_comp: bool | None = None
    quick_start: bool | None = None
    higher_volt_offset: Annotated[int, Field(ge=0, le=100)] | None = None
    tuner_bad_chip_hr_threshold: Annotated[int, Field(ge=20, le=80)] | None = None
    remain_stopped_on_reboot: bool | None = None
    ignore_broken_sensors: bool | None = None
    disable_volt_checks: bool | None = None
    quiet_mode: bool | None = None
    downscale_preset_on_failure: bool | None = None
    auto_chip_throttling: bool | None = None
    max_startup_delay_time: Annotated[int, Field(ge=0, le=300)] | None = None
    ignore_chip_sensors: bool | None = None
    min_operational_chains: Annotated[int, Field(ge=0)] | None = None


class OverclockChain(BaseModel):
    chips: list[Annotated[int, Field(ge=0)]] | None = None
    freq: Annotated[int, Field(ge=0)] | None = None
    disabled: bool | None = None


class OverclockSettings(BaseModel):
    modded_psu: bool | None = None
    preset: str | None = None
    globals: Globals | None = None
    chains: list[OverclockChain] | None = None
    preset_switcher: PresetSwitcher | None = None


class PoolSettings(BaseModel):
    url: str = ""
    user: str = ""
    passwd: str = Field("", alias="pass")


class MinerSettings(BaseModel):
    cooling: CoolingSettings | None = None
    misc: AdvancedSettings | None = None
    overclock: OverclockSettings | None = None
    pools: list[PoolSettings] | None = None


class NetworkSettings(BaseModel):
    hostname: str
    dhcp: bool
    ipaddress: str
    netmask: str
    gateway: str
    dnsservers: list[str]
    enable_network_check: bool | None = None


class Settings(BaseModel):
    miner: MinerSettings | None = None
    network: NetworkSettings | None = None


class SettingsResponse(BaseModel):
    restart_required: bool
    reboot_required: bool


class BlinkStatus(BaseModel):
    blink: bool


class VnishHTTPClient(BaseHTTPClient):
    def __init__(self, ip: str, port: int = 80, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)

        self.username: str = "admin"
        if alt_pwd:
            settings.set_auth_alt("vnish", alt_pwd)
        self.passwds = settings.get_auth_list("vnish")

        self.command_path = Template("api/v1/${command}")

    def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            try:
                resp = self._do_http("POST", path="api/v1/unlock", payload={"pw": pwd})
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
                    try:
                        resobj = resp.json()
                    except requests.exceptions.JSONDecodeError:
                        break
                    else:
                        if "token" in resobj:
                            self.authed = True
                            self.token = resobj["token"]
                            self.pwd = pwd
                            break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    def get_hostname(self) -> str:
        resp = self.get_network_info()
        return resp["hostname"]

    def get_mac_addr(self) -> str:
        resp = self.get_network_info()
        return resp["mac"]

    def get_api_version(self) -> str:
        return super().get_api_version()

    def get_system_info(self) -> dict:
        resp = self.send_command("GET", command="info")
        try:
            resobj = Info.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump()

    def get_network_info(self) -> dict:
        resp = self.get_system_info()
        return resp["system"]["network_status"]

    def log(
        self, log_type: Literal["status", "miner", "autotune", "system", "messages"]
    ) -> dict:
        return self.send_command("GET", command=f"logs/{log_type}")

    def summary(self) -> dict:
        resp = self.send_command("GET", command="summary")
        try:
            resobj = Summary.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(exclude_none=True)

    def get_miner_conf(self) -> dict:
        resp = self.send_command("GET", command="settings")
        try:
            resobj = Settings.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(by_alias=True, exclude_none=True)

    def set_miner_conf(self, conf: dict) -> dict:
        resp = self.send_command("POST", command="settings", payload=conf)
        try:
            resobj = SettingsResponse.model_validate(obj=resp)
        except ValidationError:
            try:
                resobj = VnishError.model_validate(**resp)
            except ValidationError as e:
                logger.error(
                    f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
                )
                raise APIInvalidResponse
            else:
                logger.error(
                    f"{self.__repr__()} : received API error {resobj.as_str()}"
                )
                raise APIError("Command failed!")
        else:
            return resobj.model_dump()

    def pools(self) -> list[dict]:
        resp = self.summary()
        ta = TypeAdapter(list[PoolStats])
        pools = ta.validate_python(resp["miner"]["pools"])
        return ta.dump_python(pools)

    def get_pool_conf(self) -> list[dict]:
        resp = self.get_miner_conf()
        ta = TypeAdapter(list[PoolSettings])
        pools = ta.validate_python(resp["miner"]["pools"], by_name=True)
        return ta.dump_python(pools, by_alias=True)

    def get_miner_status(self) -> dict:
        resp = self.send_command("GET", command="status")
        try:
            resobj = MinerStatus.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(
                f"{self.__repr__()} : {str(APIInvalidResponse(reason=str(e)))}"
            )
            raise APIInvalidResponse
        else:
            return resobj.model_dump(exclude_none=True)

    def get_blink_status(self) -> dict:
        resp = self.get_miner_status()
        blink = BlinkStatus(blink=resp["find-miner"])
        return blink.model_dump()

    def blink(self, enabled: bool, *args, **kwargs) -> dict:
        return self.send_command("POST", command="find-miner")

    def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        conf = self.get_miner_conf()
        if conf["miner"]["pools"] is None:
            raise APIError("Failed to retreive pool config.")
        pool_conf: list[dict[str, str]] = conf["miner"]["pools"]
        for i in range(0, len(urls)):
            if (
                not any(pool_conf[i].values())
                and not len(urls[i])
                and not len(users[i])
            ):
                continue
            pool_conf[i] = {"url": urls[i], "user": users[i], "pass": passwds[i]}
        return self.set_miner_conf(conf=conf)
