# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from typing import Any, TypeAlias

from pydantic import BaseModel, Field, RootModel

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


class SystemInfoModel(BaseModel):
    pass


class NetworkInfoModel(BaseModel):
    pass


class MinerStatusModel(BaseModel):
    pass


class SummaryModel(BaseModel):
    pass


class MinerConfigModel(BaseModel):
    pass


class MinerPasswdConfigModel(BaseModel):
    pass


class MinerPoolModel(BaseModel):
    pass


class MinerPoolConfigModel(BaseModel):
    pass
