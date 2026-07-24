# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from typing import Any

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


class Command(BaseModel):
    command: str
    parameter: str | None = None


class Status(BaseModel):
    status: str = Field(alias="STATUS")
    when: int | None = Field(None, alias="When")
    code: int | None = Field(None, alias="Code")
    msg: str | dict = Field(alias="Msg")
    description: str | None = Field(None, alias="Description")

    def error(self) -> str | None:
        if self.status == "E" or self.status == "F":
            return f"received API error ({self.code}) {self.msg} - {self.description}"


class Version(BaseModel):
    api: str = Field(alias="API")
    cgminer: str | None = Field(None, alias="CGMiner")
    luxminer: str | None = Field(None, alias="LUXminer")
    gcminer: str | None = Field(None, alias="GCMiner")
    compile_time: str | None = Field(None, alias="CompileTime")
    miner: str | None = Field(None, alias="Miner")
    type: str | None = Field(None, alias="Type")


class Pool(BaseModel):
    url: str = Field(alias="URL")
    status: str = Field(alias="Status")
    user: str = Field(alias="User")
    diff: float | None = Field(None, alias="Diff")
    pool: int = Field(alias="POOL")
    priority: int = Field(alias="Priority")
    quota: int = Field(alias="Quota")
    getworks: int = Field(alias="Getworks")
    accepted: int = Field(alias="Accepted")
    rejected: int = Field(alias="Rejected")
    stale: int = Field(alias="Stale")
    diffa: float | None = Field(None, alias="Difficulty Accepted")
    diffr: float | None = Field(None, alias="Difficulty Rejected")
    stratum_diff: float | None = Field(None, alias="Stratum Difficulty")
    stratum_active: bool = Field(alias="Stratum Active")


class Response(BaseModel):
    id: int
    status: list[Status] = Field(alias="STATUS")
    version: list[Version] | None = Field(None, alias="VERSION")
    summary: list[dict[str, Any]] | None = Field(None, alias="SUMMARY")
    stats: list[dict[str, Any]] | None = Field(None, alias="STATS")
    devs: list[dict[str, Any]] | None = Field(None, alias="DEVS")
    dev_details: list[dict[str, Any]] | None = Field(None, alias="DEVDETAILS")
    pools: list[Pool] | None = Field(None, alias="POOLS")

    def error(self) -> str | None:
        for status in self.status:
            match status.status:
                case "E" | "F":
                    return f"received API error ({status.code}) {status.msg} - {status.description}"
                case _:
                    return None
