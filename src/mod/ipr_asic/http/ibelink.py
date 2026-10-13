# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import json
import logging
from typing import final, override

import httpx
from pydantic import ValidationError

from mod.ipr_asic.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)
from mod.ipr_asic.protocol.http import BaseHTTPClient
from mod.ipr_asic.schemas.ibelink import (
    ActionResponse,
    AuthResponse,
    MinerPasswdConfig,
    MinerPoolConfigForm,
    NetworkInfo,
    NetworkResponse,
    OverviewResponse,
    PoolConfigResponse,
    SystemInfo,
    VersionInfo,
)
from mod.ipr_asic.schemas.models import (
    APIObject,
    MinerPoolModel,
    PoolConfig,
    SummaryModel,
)
from mod.ipr_asic.settings import get_auth_list, set_alt_auth

logger = logging.getLogger(__name__)


@final
class IBeLinkHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, transport=transport)

        self.username: str = "iBeLink"
        if alt_pwd:
            set_alt_auth("ibelink", alt_pwd)
        self.passwds: list[str] = get_auth_list("ibelink")

        self.command_path: str = "api/{command}"
        self.token: str | None = None

    @override
    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            data = {
                "username": self.username,
                "password": pwd,
            }
            try:
                resp = await self._do_http(method="POST", path="api/auth", data=data)
                _ = resp.raise_for_status()
            except (httpx.ConnectError, httpx.TimeoutException):
                raise FailedConnectionError("Failed to connect or timeout occurred")
            except httpx.HTTPError:
                continue
            else:
                if resp.status_code == 200:
                    try:
                        resobj = resp.json()
                        auth_resp = AuthResponse.model_validate(obj=resobj)
                    except (json.JSONDecodeError, ValidationError):
                        break
                    else:
                        if auth_resp.error():
                            continue
                        self.cookies = (
                            "_locale=en_US; JSESSIONID=" + auth_resp.session_id
                        )
                        self.token = auth_resp.jwt
                        self.pwd = pwd
                        self.authed = True
                        break
            if not self.authed:
                raise AuthenticationError("Failed to authenticate")

    def _validate_response(self, data: APIObject) -> ActionResponse:
        try:
            resobj = ActionResponse.model_validate(data)
        except ValidationError as e:
            logger.error(f"{self.__repr__()}: {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            if err := resobj.error():
                logger.error(f"{self.__repr__()}: {err}")
                raise APIError(f"Command failed: {err}")
        return resobj

    @override
    async def hostname(self) -> str:
        resp = await self.get_system_info()
        return resp.mac

    @override
    async def mac_address(self) -> str:
        resp = await self.get_system_info()
        return resp.mac

    async def get_version_info(self) -> tuple[str, VersionInfo]:
        resp = await self.send_command("GET", command="overview")
        _ = self._validate_response(resp)
        try:
            ver_info = OverviewResponse.model_validate(obj=resp)
            return ver_info.version_info.api_version, ver_info.version_info
        except ValidationError as e:
            logger.error(f"{self.__repr__()}: {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse

    async def get_system_info(self) -> SystemInfo:
        resp = await self.send_command("GET", command="overview")
        _ = self._validate_response(resp)
        try:
            return OverviewResponse.model_validate(obj=resp).miner_info
        except ValidationError as e:
            logger.error(f"{self.__repr__()}: {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse

    async def get_network_info(self) -> NetworkInfo:
        resp = await self.send_command("GET", command="network")
        _ = self._validate_response(resp)
        try:
            return NetworkResponse.model_validate(obj=resp).network_info
        except ValidationError as e:
            logger.error(f"{self.__repr__()}: {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse

    async def summary(self) -> SummaryModel:
        # http api doesnt expose summary data
        return SummaryModel()

    async def pools(self) -> list[MinerPoolModel]:
        # http api doesnt expose active pool data
        return []

    async def get_pool_conf(self) -> PoolConfig:
        resp = await self.send_command("GET", command="getPools")
        _ = self._validate_response(resp)
        try:
            return PoolConfigResponse.model_validate(obj=resp).pools
        except ValidationError as e:
            logger.error(f"{self.__repr__()}: {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse

    @override
    async def restart(self) -> APIObject:
        resp = await self.send_command("POST", command="appreboot")
        resobj = self._validate_response(resp)
        return resobj.model_dump()

    @override
    async def reboot(self) -> APIObject:
        resp = await self.send_command("POST", command="reboot")
        resobj = self._validate_response(resp)
        return resobj.model_dump()

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        conf = await self.get_pool_conf()
        pool_conf: list[dict[str, str]] = conf.model_dump()[:3]

        new_conf = MinerPoolConfigForm()
        for i in range(len(urls)):
            if (
                not any(pool_conf[i].values())
                and not len(urls[i])
                and not len(users[i])
            ):
                continue
            idx = i + 1
            new_conf.__setattr__(f"pool{idx}", urls[i])
            new_conf.__setattr__(f"user{idx}", users[i])
            new_conf.__setattr__(f"pass{idx}", passwds[i])

        resp = await self.send_command(
            "POST", command="updatePools", data=new_conf.model_dump(by_alias=True)
        )
        resobj = self._validate_response(resp)
        return resobj.model_dump()

    @override
    async def update_passwd(self, old_passwd: str, new_passwd: str) -> APIObject:
        pw_conf = MinerPasswdConfig(
            username=self.username, curr_passwd=old_passwd, new_passwd=new_passwd
        )
        resp = await self.send_command(
            method="POST",
            command="update",
            path="password",
            data=pw_conf.model_dump(by_alias=True),
        )
        resobj = self._validate_response(resp)
        return resobj.model_dump()

    @override
    async def update_firmware(
        self, firmware: bytes, filename: str, keep_settings: bool
    ) -> APIObject:
        if not firmware:
            raise APIError("Firmware image is empty")
        resp = await self.send_command(
            method="POST",
            command="upgrade",
            files={"file": (filename, firmware, "application/gzip")},
            timeout=300.0,
        )
        resobj = self._validate_response(resp)
        return resobj.model_dump()
