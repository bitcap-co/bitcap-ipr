from typing import Any

from pydantic import BaseModel, Field


class Command(BaseModel):
    command: str
    parameter: str | None = None


class Status(BaseModel):
    status: str = Field(alias="STATUS")
    when: int | None = Field(default=None, alias="When")
    code: int | None = Field(default=None, alias="Code")
    msg: str | dict[str, Any] = Field(alias="Msg")
    description: str | None = Field(default=None, alias="Description")

    def error(self) -> str | None:
        if self.status == "E" or self.status == "F":
            return f"API error ({self.code}): {self.msg} - {self.description}"


class Version(BaseModel):
    api: str = Field(alias="API")
    cgminer: str | None = Field(default=None, alias="CGMiner")
    luxminer: str | None = Field(default=None, alias="LUXMiner")
    gcminer: str | None = Field(default=None, alias="GCMiner")
    compile_time: str | None = Field(default=None, alias="CompileTime")
    miner: str | None = Field(default=None, alias="Miner")
    type: str | None = Field(default=None, alias="Type")


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


class BaseCGMinerResponse(BaseModel):
    id: int
    status: list[Status] = Field(alias="STATUS")
    version: list[Version] | None = Field(None, alias="VERSION")

    def error(self) -> str | None:
        for status in self.status:
            match status.status:
                case "E" | "F":
                    return (
                        f"API error ({status.code}) {status.msg} - {status.description}"
                    )
                case _:
                    return None


class CGMinerResponse(BaseCGMinerResponse):
    summary: list[dict[str, Any]] | None = Field(None, alias="SUMMARY")
    stats: list[dict[str, Any]] | None = Field(None, alias="STATS")
    devs: list[dict[str, Any]] | None = Field(None, alias="DEVS")
    dev_details: list[dict[str, Any]] | None = Field(None, alias="DEVDETAILS")
    pools: list[Pool] | None = Field(None, alias="POOLS")
