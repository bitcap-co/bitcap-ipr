import logging

from pydantic import BaseModel, Field, ValidationError

from apiv2.errors import APIError, APIInvalidResponse
from apiv2.rpc.cgminer import CGMinerRPCClient, Status

logger = logging.getLogger(__name__)


class ConfigItem(BaseModel):
    asc_count: int = Field(alias="ASC Count")
    actual_power_target: int = Field(alias="ActualPowerTarget")
    bcast_addr: str = Field(alias="BcastAddr")
    control_board_type: str = Field(alias="ControlBoardType")
    cooling: str = Field(alias="Cooling")
    curtail_mode: str = Field(alias="CurtailMode")
    dhcp: bool = Field(alias="DHCP")
    dns_servers: str = Field(alias="DNS Servers")
    device_code: str = Field(alias="Device Code")
    fpga_build_id_hex: str = Field(alias="FPGABuildIdHex")
    fpga_build_id_str: str = Field(alias="FPGABuildIdStr")
    fee_status: str = Field(alias="FeeStatus")
    gateway: str = Field(alias="Gateway")
    green_led: str = Field(alias="GreenLed")
    hostname: str = Field(alias="Hostname")
    hotplug: str = Field(alias="Hotplug")
    ip_addr: str = Field(alias="IPAddr")
    ideal_power_target: int = Field(alias="IdealPowerTarget")
    immersion_mode: bool = Field(alias="ImmersionMode")
    is_atm_enabled: bool = Field(alias="IsAtmEnabled")
    is_power_supply_on: bool = Field(alias="IsPowerSupplyOn")
    is_power_target_enabled: bool = Field(alias="IsPowerTargetEnabled")
    is_power_target_supported: bool = Field(alias="IsPowerTargetSupported")
    is_single_voltage: bool = Field(alias="IsSingleVoltage")
    is_tuning: bool = Field(alias="IsTuning")
    log_interval: int = Field(alias="Log Interval")
    log_file_level: str = Field(alias="LogFileLevel")
    mac_addr: str = Field(alias="MACAddr")
    model: str = Field(alias="Model")
    nameplate_ths: float = Field(alias="NameplateTHS")
    netmask: str = Field(alias="Netmask")
    os: str = Field(alias="OS")
    pga_count: int = Field(alias="PGA Count")
    pic: str = Field(alias="PIC")
    psu_hw_version: str = Field(alias="PSUHwVersion")
    psu_label: str = Field(alias="PSULabel")
    pool_count: int = Field(alias="Pool Count")
    power_limit: int = Field(alias="PowerLimit")
    profile: str = Field(alias="Profile")
    profile_step: str = Field(alias="ProfileStep")
    red_led: str = Field(alias="RedLed")
    serial_number: str = Field(alias="SerialNumber")
    strategy: str = Field(alias="Strategy")
    system_status: str = Field(alias="SystemStatus")
    update_on_startup: str = Field(alias="UpdateOnStartup")
    update_on_timeout: str = Field(alias="UpdateOnTimeout")
    update_on_user: str = Field(alias="UpdateOnUser")
    update_source: str = Field(alias="UpdateSource")
    update_timeout: int = Field(alias="UpdateTimeout")


class ConfigResposnse(BaseModel):
    config: list[ConfigItem] = Field(alias="CONFIG")
    status: list[Status] = Field(alias="STATUS")
    id: int

    def error(self) -> str | None:
        for status in self.status:
            match status.status:
                case "E" | "F":
                    return f"received API error ({status.code}) {status.msg} - {status.description}"
                case _:
                    return None


class BlinkStatus(BaseModel):
    blink: bool


class ActionResponse(BaseModel):
    success: bool
    msg: str = ""


class LuxminerRPCClient(CGMinerRPCClient):
    def __init__(self, ip: str, port: int = 4028, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)
        self.session_token: str | None = None

    def send_command(self, command: str, *args, **kwargs) -> dict:
        if kwargs.get("parameters") is not None and len(args) == 0:
            return super().send_command(command, **kwargs)
        return super().send_command(command, parmeters=",".join(args), **kwargs)

    def send_privileged_command(self, command: str, *args, **kwargs) -> dict:
        if self.session_token is None:
            self.authenticate()
        return self.send_command(command, self.session_token, *args, **kwargs)

    def authenticate(self) -> str | None:
        try:
            data = self.send_command("session")
            if not data["SESSION"][0]["SessionID"] == "":
                self.session_token = data["SESSION"][0]["SessionID"]
                return self.session_token
        except APIError:
            pass

        try:
            data = self.send_command("logon")
            self.session_token = data["SESSION"][0]["SessionID"]
            return self.session_token
        except (LookupError, APIError):
            pass
        return None

    def version(self) -> dict:
        return super().version()

    def summary(self) -> dict:
        return super().summary()

    def stats(self) -> list[dict]:
        return super().stats()

    def devs(self) -> list[dict]:
        return super().devs()

    def devdetails(self) -> list[dict]:
        return super().devdetails()

    def pools(self) -> list[dict]:
        return super().pools()

    def get_system_info(self) -> dict:
        resp = self.send_command("config")
        try:
            resobj = ConfigResposnse.model_validate(obj=resp, by_alias=True)
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
            return resp["CONFIG"]

    def get_blink_status(self) -> dict:
        resp = self.get_system_info()
        blink = BlinkStatus(blink=True if resp["RedLed"] == "blink" else False)
        return blink.model_dump()

    def blink(
        self,
        enabled: bool,
        auto: bool = True,
        led: str = "red",
    ) -> dict:
        if enabled:
            auto = False
        if auto:
            return self.send_privileged_command("ledset", led, "auto")
        return self.send_privileged_command("ledset", led, "blink")

    def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        for i in range(0, len(urls)):
            if not len(urls[i]) and not len(users[i]):
                continue
            pool: list[str] = [urls[i], users[i], passwds[i]]
            resp = self.send_command("addpool", *pool)
            _ = self._validate_response(resp)
        resobj = ActionResponse(success=True, msg="OK")
        return resobj.model_dump()
