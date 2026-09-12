# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from typing import Any, ClassVar, TypeAlias

from pydantic import BaseModel, ConfigDict, Field, RootModel

APIObject: TypeAlias = dict[str, Any]


class ContentResponse(BaseModel):
    text: str


class ActionResult(BaseModel):
    success: bool
    msg: str = ""


class MinerPoolConfig(BaseModel):
    url: str = ""
    user: str = ""
    pwd: str = Field(default="", serialization_alias="pass")


class PoolConfig(RootModel[list[MinerPoolConfig]]):
    pass


class BlinkStatusModel(BaseModel):
    pass


class BlinkStatus(BlinkStatusModel):
    blink: bool


class RawModel(BaseModel):
    model_config: ClassVar[ConfigDict] = ConfigDict(extra="allow")


class SystemInfoModel(RawModel):
    pass


class VersionInfoModel(RawModel):
    pass


class NetworkInfoModel(RawModel):
    pass


class MinerStatusModel(RawModel):
    pass


class SummaryModel(RawModel):
    pass


class MinerConfigModel(RawModel):
    pass


class MinerPoolModel(RawModel):
    pass


class MinerPasswdConfigModel(RawModel):
    pass


class MinerPoolConfigModel(RawModel):
    pass
