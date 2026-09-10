# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
from typing import Literal, override

from pydantic import TypeAdapter

from mod.ipr_asic.errors import APIError
from mod.ipr_asic.rpc.cgminer import CGMinerRPCClient
from mod.ipr_asic.schemas.cgminer import Version
from mod.ipr_asic.schemas.luxminer import Config, Dev, Devdetail, MinerPool, Summary
from mod.ipr_asic.schemas.models import ActionResult, APIObject, BlinkStatus

logger = logging.getLogger(__name__)


class LuxminerRPCClient(CGMinerRPCClient):
    def __init__(self, ip: str, port: int = 4028, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)
        self.session_token: str | None = None

    @override
    async def send_command(self, command: str, *args, **kwargs) -> APIObject:
        if kwargs.get("parameters") is not None and len(args) == 0:
            return await super().send_command(command, **kwargs)
        return await super().send_command(command, parameters=",".join(args), **kwargs)

    @override
    async def send_privileged_command(self, command: str, *args, **kwargs) -> APIObject:
        if self.session_token is None:
            _ = await self.authenticate()
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

    @override
    async def version(self) -> Version:
        version = await super().version()
        return Version.model_validate(version)

    @override
    async def summary(self) -> Summary:
        return await self._get_one("summary", "SUMMARY", TypeAdapter(Summary))

    @override
    async def devs(self) -> list[Dev]:
        return await self._get_many("devs", "DEVS", TypeAdapter(list[Dev]))

    @override
    async def devdetails(self) -> list[Devdetail]:
        return await self._get_many(
            "devdetails", "DEVDETAILS", TypeAdapter(list[Devdetail])
        )

    @override
    async def pools(self) -> list[MinerPool]:
        return await self._get_many("pools", "POOLS", TypeAdapter(list[MinerPool]))

    @override
    async def get_system_info(self) -> Config:
        return await self._get_one("config", "CONFIG", TypeAdapter(Config))

    async def get_blink_status(self) -> BlinkStatus:
        resp = await self.get_system_info()
        blink = BlinkStatus(blink=resp.red_led == "blink")
        return blink

    @override
    async def blink(
        self,
        enabled: bool,
        auto: bool = True,
        led: str = "red",
    ) -> APIObject:
        if enabled:
            auto = False
        if auto:
            return await self.send_privileged_command("ledset", led, "auto")
        return await self.send_privileged_command("ledset", led, "blink")

    async def set_miner_mode(
        self, mode: Literal["sleep", "wakeup"] = "wakeup"
    ) -> APIObject:
        resp = await self.send_privileged_command("curtail", mode)
        error = self._validate_response(resp)
        if error is not None:
            logger.error(f"{self.__repr__()}: {APIError(error)!s}")
            raise APIError("Command failed")
        return resp

    @override
    async def start(self) -> APIObject:
        return await self.set_miner_mode("wakeup")

    @override
    async def stop(self) -> APIObject:
        return await self.set_miner_mode("sleep")

    @override
    async def restart(self) -> APIObject:
        return await self.send_privileged_command("resetminer")

    @override
    async def reboot(self) -> APIObject:
        return await self.send_privileged_command("rebootdevice")

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        for i in range(len(urls)):
            if not len(urls[i]) and not len(users[i]):
                continue
            pool: list[str] = [urls[i], users[i], passwds[i]]
            resp = await self.send_command("addpool", *pool)
            error = self._validate_response(resp)
            if error is not None:
                logger.error(f"{self.__repr__()}: {APIError(error)!s}")
                raise APIError("Command failed")
        resobj = ActionResult(success=True, msg="OK")
        return resobj.model_dump()
