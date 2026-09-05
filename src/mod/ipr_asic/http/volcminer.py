# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import logging
import re
from typing import final, override

import httpx
from pydantic import ValidationError
from pydantic_core import from_json

from mod.ipr_asic import settings
from mod.ipr_asic.errors import (
    APIError,
    APIInvalidResponse,
    AuthenticationError,
    FailedConnectionError,
)
from mod.ipr_asic.protocol import BaseHTTPClient
from mod.ipr_asic.schemas.models import APIObject, ContentResponse, PoolConfig
from mod.ipr_asic.schemas.volcminer import (
    MinerConfig,
    MinerConfigV1,
    MinerPool,
    MinerStatus,
    NetworkInfo,
    NetworkInfoV1,
    SystemInfo,
)

logger = logging.getLogger(__name__)

_DATA_RESPONSE_RE = re.compile(r'"data":"\{(.*?)\}"')
_CONFIG_RESPONSE_RE = re.compile(
    r'"cfgs":"\[(.*?)\]",(.*?),"debug":"\{(.*?)\}",(.*?)\}'
)
_SUMMARY_RESPONSE_RE = re.compile(
    r'(.*?),"pool_dtls":"\[(.*?)\]"\},"chains":"\[(.*?)\]",(.*?)$'
)


@final
class VolcminerHTTPClient(BaseHTTPClient):
    def __init__(
        self,
        ip: str,
        port: int = 80,
        alt_pwd: str | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        super().__init__(ip, port, alt_pwd, transport)
        self.username: str = "root"
        if alt_pwd:
            settings.set_alt_auth("volcminer", alt_pwd)
        self.passwds: list[str] = settings.get_auth_list("volcminer")

        self.command_path: str = "cgi-bin/{command}.cgi"

    @override
    async def authenticate(self) -> None:
        for pwd in self.passwds:
            if not pwd:
                continue
            digest = httpx.DigestAuth(self.username, pwd)
            try:
                async with self._new_client(auth=digest) as client:
                    resp = await client.get(self.base_url)
                    _ = resp.raise_for_status()
            except (
                httpx.ConnectError,
                httpx.TimeoutException,
            ):
                raise FailedConnectionError("Failed to connect or timeout occurred")
            except httpx.HTTPError:
                continue
            else:
                if resp.status_code == 200:
                    self.authed = True
                    self.digest = digest
                    self.pwd = pwd
                    break
        if not self.authed:
            raise AuthenticationError("Failed to authenticate")

    def _clean_response(self, resp: APIObject) -> str:
        try:
            resobj = ContentResponse.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return re.sub(r"\s{1,}", "", resobj.text)

    async def get_hostname(self) -> str:
        resp = await self.get_network_info()
        return resp.conf_hostname

    async def get_mac_addr(self) -> str:
        resp = await self.get_network_info()
        return resp.macaddr

    async def get_api_version(self) -> str:
        resp = await self.get_system_info()
        return resp.cgminer_version or ""

    async def get_system_info(self) -> SystemInfo:
        resp = await self.send_command("GET", command="get_system_info")
        try:
            resobj = SystemInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_network_info(self) -> NetworkInfo:
        resp = await self.send_command("GET", command="get_network_info")
        try:
            resobj = NetworkInfo.model_validate(obj=resp)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_network_infoV1(self) -> NetworkInfoV1:
        """Volcminer: get network info from 'get_network_infoV1' endpoint"""
        resp = await self.send_command(method="GET", command="get_network_infoV1")
        cleaned = self._clean_response(resp)
        try:
            if match := (re.search(_DATA_RESPONSE_RE, cleaned)):
                data = match.group(1)
            else:
                raise APIError("Failed to get valid response.")
            net_info = from_json(f"{{{data}}}")
            resobj = NetworkInfoV1.model_validate(obj=net_info)
        except (ValueError, ValidationError) as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_miner_conf(self) -> MinerConfig:
        resp = await self.send_command("GET", command="get_miner_conf")
        try:
            resobj = MinerConfig.model_validate(obj=resp, by_alias=True)
        except ValidationError as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def get_miner_confV1(self) -> MinerConfigV1:
        """Volcminer: get miner config from 'get_miner_confV1' endpoint"""
        resp = await self.send_command(method="GET", command="get_miner_confV1")
        cleaned = self._clean_response(resp)
        try:
            if match := re.search(_CONFIG_RESPONSE_RE, cleaned):
                parts = match.groups()
                cfgs = parts[0]
                keep_power = parts[1]
                debug = parts[2]
                extra = parts[3]
            else:
                raise APIError("Failed to get valid response.")
            miner_conf = from_json(
                f'{{"miner":{cfgs},{keep_power},"debug":{{{debug}}},{extra}}}'
            )
            resobj = MinerConfigV1.model_validate(obj=miner_conf, by_alias=True)
        except (ValueError, ValidationError) as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def set_miner_conf(self, conf: APIObject) -> APIObject:
        return await self.send_command("POST", command="set_miner_conf", data=conf)

    # async def log(self, *args, **kwargs) -> dict:
    #     return await super().log(*args, **kwargs)

    async def summary(self) -> MinerStatus:
        resp = await self.send_command("GET", command="get_miner_statusV1")
        cleaned = self._clean_response(resp)
        try:
            if match := re.search(_DATA_RESPONSE_RE, cleaned):
                data = match.group(1)
                parts = re.search(_SUMMARY_RESPONSE_RE, data).groups()
                status = parts[0]
                pools = parts[1]
                chains = parts[2]
                fans = parts[3]
            else:
                raise APIError("Failed to get valid response.")
            miner_status = from_json(
                f"{{{status},pool_dtls:[{pools}]}},chains:[{chains}],{fans}}}"
            )
            resobj = MinerStatus.model_validate(obj=miner_status)
        except (AttributeError, ValueError, ValidationError) as e:
            logger.error(f"{self.__repr__()} : {APIInvalidResponse(reason=str(e))!s}")
            raise APIInvalidResponse
        else:
            return resobj

    async def pools(self) -> list[MinerPool]:
        resp = await self.summary()
        return resp.pools.pool_dtls

    async def get_pool_conf(self) -> PoolConfig:
        resp = await self.get_miner_conf()
        return resp.pools

    @override
    async def blink(self, enabled: bool) -> APIObject:
        data = {"_bb_type": "rgOn" if enabled else "rgOff"}
        return await self.send_command("POST", command="post_led_onoff", data=data)

    @override
    async def restart(self) -> APIObject:
        return await self.reboot()

    @override
    async def reboot(self) -> APIObject:
        return await self.send_command("POST", command="reboot")

    @override
    async def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> APIObject:
        if len(urls) != 3 or len(users) != 3 or len(passwds) != 3:
            raise APIError("Invalid length of arguments")

        conf = await self.get_miner_confV1()
        miner = conf.miner

        data: APIObject = {}
        for i in range(len(urls)):
            if len(urls[i]) and len(users[i]) and passwds[i] == "":
                passwds[i] = "x"
            data[f"_bb_pool{i + 1}url"] = urls[i]
            data[f"_bb_pool{i + 1}user"] = users[i]
            data[f"_bb_pool{i + 1}pw"] = passwds[i]

        data["_bb_nobeeper"] = ""
        data["_bb_notempoverctrl"] = "false"
        if miner.fan_ctrl:
            data["_bb_fan_customize_switch"] = "true"
            data["_bb_fan_customize_value_front"] = miner.fan_pwm_front
            data["_bb_fan_customize_value_back"] = miner.fan_pwm_back
        else:
            data["_bb_fan_customize_switch"] = "false"
            data["_bb_fan_customize_value_front"] = ""
            data["_bb_fan_customize_value_back"] = ""

        data["_bb_freq"] = miner.freq
        data["_bb_coin_type"] = miner.coin_type
        data["_bb_runmode"] = conf.runmode
        data["_bb_voltage_customize_value"] = conf.voltage
        data["_bb_ema"] = miner.sram_voltage
        data["_bb_debug"] = "false"

        return await self.set_miner_conf(conf=data)
