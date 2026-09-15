# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import os
from enum import Enum
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, Field, TypeAdapter

from utils import get_config_dir, get_config_file_path


class PresetType(int, Enum):
    POOL = 0
    SOCKET = 1


class Preset(BaseModel):
    preset_name: str = ""


class PoolPreset(Preset):
    pool1: str = ""
    user1: str = ""
    passwd1: str = ""
    pool2: str = ""
    user2: str = ""
    passwd2: str = ""
    pool3: str = ""
    user3: str = ""
    passwd3: str = ""


class SocketPreset(Preset):
    socket_addr: str = ""


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
    check_updates_on_startup: Annotated[
        bool, Field(alias="checkForUpdatesOnStartup")
    ] = True
    include_prereleases: Annotated[bool, Field(alias="includePreReleases")] = False


class IPRD(BaseModel):
    enable_iprd: Annotated[bool, Field(alias="enableIPRD")] = False
    auto_discover: Annotated[bool, Field(alias="autoDiscover")] = False
    socket_addr: Annotated[str, Field(alias="socketAddress")] = ""
    auto_reconnect: Annotated[bool, Field(alias="autoReconnect")] = True
    max_reconnect_attempts: Annotated[
        int, Field(ge=1), Field(le=10), Field(alias="maxReconnectAttempts")
    ] = 3
    selected_preset: Annotated[int, Field(alias="selectedSocketPreset")] = -1
    socket_presets: Annotated[list[SocketPreset], Field(alias="socketPresets")] = []


class Listeners(BaseModel):
    antminer: Annotated[bool, Field(strict=True)] = True
    whatsminer: Annotated[bool, Field(strict=True)] = True
    iceriver: Annotated[bool, Field(strict=True)] = True
    hammer: Annotated[bool, Field(strict=True)] = True
    volcminer: Annotated[bool, Field(strict=True)] = True
    goldshell: Annotated[bool, Field(strict=True)] = True
    sealminer: Annotated[bool, Field(strict=True)] = True
    elphapex: Annotated[bool, Field(strict=True)] = True
    auradine: Annotated[bool, Field(strict=True)] = True
    ipollo: Annotated[bool, Field(strict=True)] = True
    hivegpu: Annotated[bool, Field(strict=True)] = True


class ListenerSettings(BaseModel):
    enable_filter: Annotated[bool, Field(alias="enableFiltering")] = False
    enable_all: Annotated[bool, Field(alias="enableAll")] = True
    listen_for: Annotated[Listeners, Field(alias="listenFor")] = Listeners()
    iprd: Annotated[IPRD, Field(alias="iprd")] = IPRD()


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
    auradine_alt_passwd: Annotated[str, Field(alias="auradineAltPasswd")] = ""
    ipollo_alt_passwd: Annotated[str, Field(alias="ipolloAltPasswd")] = ""


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


class PoolConfiguratorSettings(BaseModel):
    auto_set_workers: Annotated[bool, Field(alias="autoSetWorkers")] = False
    selected_preset: Annotated[int, Field(alias="selectedPoolPreset")] = -1
    pool_presets: Annotated[list[PoolPreset], Field(alias="poolPresets")] = []


class IDTableInstanceSettings(BaseModel):
    table_live_capture: Annotated[bool, Field(alias="enableTableLiveCapture")] = False
    clear_table_on_stop: Annotated[bool, Field(alias="clearTableOnStop")] = False


class InstanceViews(BaseModel):
    show_table: Annotated[bool, Field(alias="showIDTable")] = False
    show_configurator: Annotated[bool, Field(alias="showConfigurator")] = False


class InstanceOptions(BaseModel):
    always_open_ip: Annotated[bool, Field(alias="alwaysOpenIP")] = False
    disable_inactive: Annotated[bool, Field(alias="disableInactiveTimer")] = False
    auto_start: Annotated[bool, Field(alias="autoStartOnLaunch")] = False
    confirms_on_top: Annotated[bool, Field(alias="confirmsStayOnTop")] = False
    table: Annotated[IDTableInstanceSettings, Field(alias="idTable")] = (
        IDTableInstanceSettings()
    )


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
        self._set_default()
        self.config_dir: str = get_config_dir()
        self.config_path: Path = get_config_file_path()

    @property
    def as_dict(self) -> dict[str, Any]:
        """Get the IPRConfigModel as dictionary.

        Returns:
            Dict[str, Any]: The dumped IPRConfigModel.
        """
        return self.config.model_dump(by_alias=True)

    def _set_default(self) -> None:
        self.general: GeneralSettings = GeneralSettings()
        self.listen_for: Listeners = Listeners()
        self.listener: ListenerSettings = ListenerSettings()
        self.listen_for = self.listener.listen_for
        self.auth_firmware: APIAuthFirmware = APIAuthFirmware()
        self.auth: APIAuth = APIAuth()
        self.api: APISettings = APISettings(auth=self.auth, firmware=self.auth_firmware)
        self.pool_config: PoolConfiguratorSettings = PoolConfiguratorSettings()
        self.logs: LogSettings = LogSettings()
        self.options: InstanceOptions = InstanceOptions()
        self.table: IDTableInstanceSettings = IDTableInstanceSettings()
        self.views: InstanceViews = InstanceViews()
        self.instance: InstanceSettings = InstanceSettings(
            options=self.options, views=self.views
        )
        self.config: IPRConfigModel = IPRConfigModel(
            general=self.general,
            listener=self.listener,
            api=self.api,
            pool_config=self.pool_config,
            logs=self.logs,
            instance=self.instance,
        )

    def _validate_model(self, conf: dict[str, Any]) -> None:
        self.config = IPRConfigModel.model_validate(conf, strict=True, by_alias=True)
        self.general = self.config.general
        self.listen_for = self.config.listener.listen_for
        self.listener = self.config.listener
        self.auth_firmware = self.config.api.firmware
        self.auth = self.config.api.auth
        self.api = self.config.api
        self.pool_config = self.config.pool_config
        self.logs = self.config.logs
        self.options = self.config.instance.options
        self.table = self.config.instance.options.table
        self.views = self.config.instance.views
        self.instance = self.config.instance

    def _read_config(self) -> None:
        os.makedirs(self.config_dir, exist_ok=True)
        if not os.path.exists(self.config_path):
            return self.write_default()
        with open(self.config_path, "r") as d:
            c = json.load(d)
        self._validate_model(c)

    def _write_config(self) -> None:
        c = self.config.model_dump_json(indent=2, by_alias=True)
        with open(self.config_path, "w") as f:
            f.write(c)

    def validate(self, conf: dict[str, Any]) -> None:
        self._validate_model(conf)

    def read(self) -> None:
        self._read_config()

    def write(self) -> None:
        self._write_config()

    def write_default(self) -> None:
        self._set_default()
        self._write_config()

    def dump_stored_presets(self, preset_type: PresetType) -> list[dict[str, str]]:
        saved: list[dict[str, str]] = []
        match preset_type:
            case PresetType.POOL:
                presets = TypeAdapter(list[PoolPreset])
                saved = presets.dump_python(
                    self.pool_config.pool_presets, by_alias=True
                )
            case PresetType.SOCKET:
                presets = TypeAdapter(list[SocketPreset])
                saved = presets.dump_python(
                    self.listener.iprd.socket_presets, by_alias=True
                )
        return saved
