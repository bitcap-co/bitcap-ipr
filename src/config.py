# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from __future__ import annotations

import json
import os
from typing import Annotated, Any, Dict

from pydantic import BaseModel, Field, ValidationError

from utils import get_config_dir, get_config_file_path


class GeneralSettings(BaseModel):
    enable_sys_tray: Annotated[bool, Field(alias="enableSystemTray")] = False
    on_close: Annotated[int, Field(le=1), Field(ge=0), Field(alias="onWindowClose")] = 0
    use_custom_timeout: Annotated[bool, Field(alias="useCustomTimeout")] = False
    inactive_timeout: Annotated[
        int,
        Field(le=120),
        Field(ge=15),
        Field(multiple_of=15),
        Field(alias="inactiveTimeoutDuration"),
    ] = 15


class IPRD(BaseModel):
    enable_iprd: Annotated[bool, Field(alias="enableIPRD")] = False
    socket_addr: Annotated[str, Field(alias="socketAddress")] = ""


class Listeners(BaseModel):
    antminer: Annotated[bool, Field(strict=True)] = True
    whatsminer: Annotated[bool, Field(strict=True)] = True
    iceriver: Annotated[bool, Field(strict=True)] = True
    hammer: Annotated[bool, Field(strict=True)] = True
    volcminer: Annotated[bool, Field(strict=True)] = True
    goldshell: Annotated[bool, Field(strict=True)] = True
    sealminer: Annotated[bool, Field(strict=True)] = True
    elphapex: Annotated[bool, Field(strict=True)] = True


class ListenerSettings(BaseModel):
    enable_filter: Annotated[bool, Field(alias="enableFiltering")] = False
    enable_all: Annotated[bool, Field(alias="enableAll")] = True
    listen_for: Annotated[Listeners, Field(alias="listenFor")] = Listeners()
    iprd: Annotated[IPRD, Field(alias="IPRD")] = IPRD()


class APIAuthFirmware(BaseModel):
    use_antminer_login: Annotated[
        bool, Field(strict=True), Field(alias="useAntminerLogin")
    ] = False
    vnish_alt_passwd: Annotated[str, Field(alias="vnishAltPasswd")] = ""


class APIAuth(BaseModel):
    antminer_alt_passwd: Annotated[str, Field(alias="antminerAltPasswd")] = ""
    iceriver_alt_passwd: Annotated[str, Field(alias="iceriverAltPasswd")] = ""
    whatsminer_alt_passwd: Annotated[str, Field(alias="whatsminerAltPasswd")] = ""
    goldshell_alt_passwd: Annotated[str, Field(alias="goldshellAltPasswd")] = ""
    hammer_alt_passwd: Annotated[str, Field(alias="hammerAltPasswd")] = ""
    volcminer_alt_passwd: Annotated[str, Field(alias="volcminerAltPasswd")] = ""
    elphapex_alt_passwd: Annotated[str, Field(alias="elphapexAltPasswd")] = ""
    sealminer_alt_passwd: Annotated[str, Field(alias="sealminerAltPasswd")] = ""


class APISettings(BaseModel):
    locate_duration: Annotated[
        int, Field(ge=5), Field(le=30), Field(alias="locateDuration")
    ] = 10
    auth: APIAuth
    firmware: APIAuthFirmware


class LogSettings(BaseModel):
    log_level: Annotated[
        str,
        Field(pattern=r"DEBUG|INFO|WARNING|ERROR|CRITICAL"),
        Field(alias="logLevel"),
    ] = "INFO"
    flush_on_close: Annotated[bool, Field(alias="flushOnClose")] = False
    max_log_size: Annotated[
        int, Field(ge=1), Field(le=4096), Field(alias="maxLogSize")
    ] = 1024
    on_max_log_size: Annotated[
        int, Field(le=1), Field(ge=0), Field(alias="onMaxLogSize")
    ] = 0


class PoolPreset(BaseModel):
    pool1: str = ""
    user1: str = ""
    passwd1: str = ""
    pool2: str = ""
    user2: str = ""
    passwd2: str = ""
    pool3: str = ""
    user3: str = ""
    passwd3: str = ""
    preset_name: str = ""


class PoolConfiguratorSettings(BaseModel):
    auto_set_workers: Annotated[bool, Field(alias="autoSetWorkers")] = False
    selected_preset: Annotated[int, Field(alias="selectedPoolPreset")] = -1
    pool_presets: Annotated[list[PoolPreset], Field(alias="poolPresets")] = []


class InstanceViews(BaseModel):
    show_table: Annotated[bool, Field(alias="showIDTable")] = False
    show_pool_conf: Annotated[bool, Field(alias="showPoolConfigurator")] = False


class InstanceOptions(BaseModel):
    always_open_ip: Annotated[bool, Field(alias="alwaysOpenIP")] = False
    disable_inactive: Annotated[bool, Field(alias="disableInactiveTimer")] = False
    auto_start: Annotated[bool, Field(alias="autoStartOnLaunch")] = False
    clear_table_on_stop: Annotated[bool, Field(alias="clearTableOnStop")] = False
    confirms_on_top: Annotated[bool, Field(alias="confirmsStayOnTop")] = False


class InstanceSettings(BaseModel):
    geometry: list[int] = []
    options: InstanceOptions
    views: InstanceViews


class IPRConfigModel(BaseModel):
    general: GeneralSettings
    listener: ListenerSettings
    api: APISettings
    pool_config: Annotated[
        PoolConfiguratorSettings, Field(alias="poolConfigurator")
    ] = PoolConfiguratorSettings()
    logs: LogSettings
    instance: InstanceSettings


class IPRConfig:
    def __init__(self):
        self.__set_default()
        self.config_dir = get_config_dir()
        self.config_path = get_config_file_path()

    @property
    def dict(self) -> Dict[str, Any]:
        """Get the IPRConfigModel as dictionary.

        Returns:
            Dict[str, Any]: The dumped IPRConfigModel.
        """
        return self.config.model_dump(by_alias=True)

    def __set_default(self) -> None:
        self.general = GeneralSettings()
        self.listen_for = Listeners()
        self.listener = ListenerSettings()
        self.listen_for = self.listener.listen_for
        self.auth_firmware = APIAuthFirmware()
        self.auth = APIAuth()
        self.api = APISettings(auth=self.auth, firmware=self.auth_firmware)
        self.pool_config = PoolConfiguratorSettings()
        self.logs = LogSettings()
        self.options = InstanceOptions()
        self.views = InstanceViews()
        self.instance = InstanceSettings(options=self.options, views=self.views)
        self.config = IPRConfigModel(
            general=self.general,
            listener=self.listener,
            api=self.api,
            pool_config=self.pool_config,
            logs=self.logs,
            instance=self.instance,
        )

    def __validate_model(self, conf: Dict[str, Any]) -> None:
        try:
            self.config = IPRConfigModel.model_validate(
                conf, strict=True, by_alias=True
            )
        except ValidationError as exc:
            raise exc
        else:
            self.general = self.config.general
            self.listen_for = self.config.listener.listen_for
            self.listener = self.config.listener
            self.auth_firmware = self.config.api.firmware
            self.auth = self.config.api.auth
            self.api = self.config.api
            self.pool_config = self.config.pool_config
            self.logs = self.config.logs
            self.options = self.config.instance.options
            self.views = self.config.instance.views
            self.instance = self.config.instance

    def __read_config(self) -> None:
        os.makedirs(self.config_dir, exist_ok=True)
        if not os.path.exists(self.config_path):
            return self.write_default()
        with open(self.config_path, "r") as d:
            try:
                c = json.load(d)
            except json.JSONDecodeError as exc:
                raise exc
        self.__validate_model(c)

    def __write_config(self) -> None:
        c = self.config.model_dump_json(indent=2, by_alias=True)
        with open(self.config_path, "w") as f:
            f.write(c)

    def validate(self, conf: Dict[str, Any]) -> None:
        self.__validate_model(conf)

    def read(self) -> None:
        self.__read_config()

    def write(self) -> None:
        self.__write_config()

    def write_default(self) -> None:
        self.__set_default()
        self.__write_config()
