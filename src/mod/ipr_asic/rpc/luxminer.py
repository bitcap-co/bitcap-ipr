# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

from mod.ipr_asic.data import ActionResponse, BlinkStatus
from mod.ipr_asic.errors import APIError, APIInvalidResponse
from mod.ipr_asic.rpc.cgminer import CGMinerRPCClient, Status

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


class LuxminerRPCClient(CGMinerRPCClient):
    def __init__(self, ip: str, port: int = 4028, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)
        self.session_token: str | None = None

    async def send_command(self, command: str, *args, **kwargs) -> dict:
        if kwargs.get("parameters") is not None and len(args) == 0:
            return await super().send_command(command, **kwargs)
        return await super().send_command(command, parameters=",".join(args), **kwargs)

    async def send_privileged_command(self, command: str, *args, **kwargs) -> dict:
        if self.session_token is None:
            await self.authenticate()
        return await self.send_command(command, self.session_token, *args, **kwargs)

    async def authenticate(self) -> str | None:
        try:
            data = await self.send_command("session")
            if data["SESSION"][0]["SessionID"] != "":
                self.session_token = data["SESSION"][0]["SessionID"]
                return self.session_token
        except APIError:
            pass

        try:
            data = await self.send_command("logon")
            self.session_token = data["SESSION"][0]["SessionID"]
            return self.session_token
        except (LookupError, APIError):
            pass
        return None

    async def version(self) -> dict:
        return await super().version()

    async def summary(self) -> dict:
        return await super().summary()

    async def stats(self) -> list[dict]:
        return await super().stats()

    async def devs(self) -> list[dict]:
        return await super().devs()

    async def devdetails(self) -> list[dict]:
        return await super().devdetails()

    async def pools(self) -> list[dict]:
        return await super().pools()

    async def get_system_info(self) -> dict:
        resp = await self.send_command("config")
        try:
            resobj = ConfigResposnse.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            err = resobj.error()
            if err:
                logger.error(f"{self.__repr__()} : {APIError(err)!s}")
                raise APIError("Command failed!")
            return resp["CONFIG"][0]

    async def get_pool_conf(self) -> list[dict]:
        return await super().get_pool_conf()

    async def get_blink_status(self) -> dict:
        resp = await self.get_system_info()
        blink = BlinkStatus(blink=resp["RedLed"] == "blink")
        return blink.model_dump()

    async def blink(
        self,
        enabled: bool,
        auto: bool = True,
        led: str = "red",
    ) -> dict:
        if enabled:
            auto = False
        if auto:
            return await self.send_privileged_command("ledset", led, "auto")
        return await self.send_privileged_command("ledset", led, "blink")

    async def set_miner_mode(self, mode: Literal["sleep", "wakeup"] = "wakeup") -> dict:
        resp = await self.send_privileged_command("curtail", mode)
        resobj = self._validate_response(resp)
        return resobj.model_dump()

    async def start(self) -> dict:
        return await self.set_miner_mode("wakeup")

    async def stop(self) -> dict:
        return await self.set_miner_mode("sleep")

    async def restart(self) -> dict:
        return await self.send_privileged_command("resetminer")

    async def reboot(self) -> dict:
        return await self.send_privileged_command("rebootdevice")

    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        for i in range(len(urls)):
            if not len(urls[i]) and not len(users[i]):
                continue
            pool: list[str] = [urls[i], users[i], passwds[i]]
            resp = await self.send_command("addpool", *pool)
            _ = self._validate_response(resp)
        resobj = ActionResponse(success=True, msg="OK")
        return resobj.model_dump()
