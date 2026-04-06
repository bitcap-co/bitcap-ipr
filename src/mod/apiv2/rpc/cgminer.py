import logging
from typing import Any

from pydantic import BaseModel, Field, TypeAdapter, ValidationError

from mod.apiv2.base import BaseRPCClient
from mod.apiv2.data import MinerConfPool
from mod.apiv2.errors import (
    APIError,
    APIInvalidResponse,
)

logger = logging.getLogger(__name__)


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


class CGMinerRPCClient(BaseRPCClient):
    def __init__(self, ip: str, port: int = 4028, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)

    def _validate_response(self, data: dict) -> Response:
        try:
            resobj = Response.model_validate(obj=data, by_alias=True)
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
            return resobj

    def version(self) -> dict:
        resp = self.send_command("version")
        valid = self._validate_response(resp)
        if not valid.version or len(valid.version) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.version[0].model_dump(by_alias=True, exclude_none=True)

    def summary(self) -> dict:
        resp = self.send_command("summary")
        valid = self._validate_response(resp)
        if valid.summary is None or len(valid.summary) != 1:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.summary[0]

    def stats(self) -> list[dict]:
        resp = self.send_command("stats")
        valid = self._validate_response(resp)
        if valid.stats is None:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.stats

    def devs(self) -> list[dict]:
        resp = self.send_command("devs")
        valid = self._validate_response(resp)
        if valid.devs is None:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.devs

    def devdetails(self) -> list[dict]:
        resp = self.send_command("devdetails")
        valid = self._validate_response(resp)
        if valid.dev_details is None:
            raise APIInvalidResponse(reason="malformed")
        else:
            return valid.dev_details

    def pools(self) -> list[dict]:
        resp = self.send_command("pools")
        valid = self._validate_response(resp)
        if valid.pools is None:
            raise APIInvalidResponse(reason="malformed")
        else:
            ta = TypeAdapter(list[Pool])
            pools = ta.validate_python(valid.pools, by_alias=True)
            return ta.dump_python(pools, by_alias=True)

    def get_system_info(self) -> dict:
        return super().get_system_info()

    def get_pool_conf(self) -> list[dict]:
        pools = self.pools()
        pool_conf = []
        for pool in pools:
            pool_conf.append(
                MinerConfPool(url=pool["URL"], user=pool["User"]).model_dump(
                    by_alias=True
                )
            )
        return pool_conf

    def get_blink_status(self) -> dict:
        return super().get_blink_status()

    def blink(self, enabled: bool, *args, **kwargs) -> dict:
        return super().blink(enabled, *args, **kwargs)

    def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        return super().update_pool_conf(urls, users, passwds)
