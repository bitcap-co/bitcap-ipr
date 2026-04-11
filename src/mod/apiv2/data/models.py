# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from pydantic import BaseModel, Field


class MinerConfPool(BaseModel):
    url: str = ""
    user: str = ""
    passwd: str = Field(default="", alias="pass")


class BlinkStatus(BaseModel):
    blink: bool


class ActionResponse(BaseModel):
    success: bool
    msg: str = ""
