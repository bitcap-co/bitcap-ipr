# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import asyncio
import logging
from typing import Any, ClassVar, Literal, override

import httpx
from pydantic import BaseModel, ConfigDict, Field
from PySide6.QtCore import QObject

from mod.ipr_asic.data import MinerData, MinerType
from mod.ipr_asic.data.miners import (
    AntminerModels,
    AntminerParser,
    AuradineModels,
    AuradineParser,
    ElphapexModels,
    ElphapexParser,
    GoldshellModels,
    GoldshellParser,
    IceriverModels,
    IceriverParser,
    IPolloModels,
    IPolloParser,
    LuxminerModels,
    LuxminerParser,
    SealminerModels,
    SealminerParser,
    SRBMinerModels,
    SRBMinerParser,
    VnishModels,
    VnishParser,
    VolcminerModels,
    VolcminerParser,
    WhatsminerModels,
    WhatsminerParser,
    WhatsminerV3Models,
    WhatsminerV3Parser,
)
from mod.ipr_asic.errors import (
    APIError,
    AuthenticationError,
    FailedConnectionError,
    UnknownClientError,
)
from mod.ipr_asic.http import (
    AntminerHTTPClient,
    AntminerOldHTTPClient,
    AuradineHTTPClient,
    ElphapexHTTPClient,
    GoldshellHTTPClient,
    IceriverHTTPClient,
    IPolloHTTPClient,
    SealminerHTTPClient,
    SRBMinerHTTPClient,
    VnishHTTPClient,
    VolcminerHTTPClient,
)
from mod.ipr_asic.protocol import MinerClient
from mod.ipr_asic.rpc import (
    LuxminerRPCClient,
    WhatsminerRPCClient,
    WhatsminerTCPClient,
)
from mod.ipr_asic.settings import get as get_setting
from mod.lm.ipreport import MinerTypeHint

logger = logging.getLogger(__name__)

ControlAction = Literal["start", "stop", "restart", "reboot"]

# client errors that a high-level operation may recover from / report
_CLIENT_ERRORS = (
    FailedConnectionError,
    AuthenticationError,
    APIError,
    OSError,
    LookupError,
    NotImplementedError,
)


class MinerResult(BaseModel):
    """Result of a high-level facade operation.

    Carries the operation payload and any client error that occurred, replacing
    the apiv2 ``client_error()``-after-the-fact pattern (which relied on a single
    shared active client and is unsafe under concurrent/bulk operations).
    """

    model_config: ClassVar[ConfigDict] = ConfigDict(arbitrary_types_allowed=True)

    data: Any = None
    error: Exception | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


class PoolConf(BaseModel):
    urls: list[str] = Field(default_factory=list)
    users: list[str] = Field(default_factory=list)
    passwds: list[str] = Field(default_factory=list)


class ASICClient(QObject):
    """Async interface for interacting with various miner backends/APIs.

    Unlike the synchronous apiv2 ``ASICClient`` (which held one active client and
    was driven from the GUI thread), each high-level coroutine here owns its
    client for the duration of one operation and then closes it. This keeps
    concurrent/bulk operations (``asyncio.gather`` over many IPs) independent and
    safe, and returns a :class:`MinerResult` instead of stashing the last error.

    Args:
        parent (QObject | None): optional parent object.
    """

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._parent: QObject | None = parent

    @override
    def __repr__(self) -> str:
        return f"{self.__class__.__name__}"

    # -- identification -----------------------------------------------------

    async def identify(self, miner_hint: MinerTypeHint, ip: str) -> MinerType:
        match miner_hint:
            case MinerTypeHint.ELPHAPEX:
                return MinerType.ELPHAPEX
            case MinerTypeHint.GOLDSHELL:
                return MinerType.GOLDSHELL
            case MinerTypeHint.ICERIVER:
                return MinerType.ICERIVER
            case MinerTypeHint.SEALMINER:
                return MinerType.SEALMINER
            case MinerTypeHint.WHATSMINER:
                return MinerType.WHATSMINER
            case MinerTypeHint.AURADINE:
                return MinerType.AURADINE
            case MinerTypeHint.IPOLLO:
                return MinerType.IPOLLO
            case MinerTypeHint.HIVEGPU:
                return MinerType.HIVEGPU
            case MinerTypeHint.COMMON:
                miner_type = await self.identify_http(ip)
                if miner_type is None:
                    return MinerType.UNKNOWN
                if miner_type == MinerType.HAMMER:
                    black_model = await self._get_blackminer_model(ip)
                    if black_model is None:
                        # fallback to HAMMER if we can't get model
                        return MinerType.HAMMER
                    if "HAMMER" in black_model.upper():
                        return MinerType.HAMMER
                    else:
                        return MinerType.VOLCMINER

                return miner_type
            case _:
                return MinerType.UNKNOWN

    async def identify_http(self, ip: str) -> MinerType | None:
        url = f"http://{ip}/"
        timeout = float(get_setting("api_function_timeout", 5.0))
        try:
            async with httpx.AsyncClient(timeout=timeout) as c:
                resp = await c.get(url, follow_redirects=True)
        except httpx.HTTPError:
            return None
        www_auth = str(resp.headers.get("www-authenticate", ""))
        if resp.status_code == 401 and 'realm="antMiner' in www_auth:
            return MinerType.ANTMINER
        if resp.status_code == 401 and 'realm="blackMiner' in www_auth:
            return MinerType.HAMMER
        if "Luxor Firmware" in resp.text:
            return MinerType.LUX_OS
        if "AnthillOS" in resp.text:
            return MinerType.VNISH
        return None

    async def _get_blackminer_model(self, ip: str) -> str | None:
        # we use a volcminer client here which is based off of the blackminer API
        # we add alt_pwd="root" to try and authenticate with HAMMER
        client = VolcminerHTTPClient(ip, alt_pwd="root")
        try:
            system_info = await client.get_system_info()
        except _CLIENT_ERRORS:
            return None
        finally:
            client.close()
        try:
            return system_info.minertype
        except (TypeError, LookupError):
            return None

    # -- client creation ----------------------------------------------------

    async def _make_client(
        self, miner_type: MinerType, ip: str, alt_pwd: str | None = None
    ) -> MinerClient:
        match miner_type:
            case MinerType.ANTMINER:
                client = AntminerHTTPClient(ip, alt_pwd=alt_pwd)
                return await self._upgrade_client(client, ip, alt_pwd)
            case MinerType.ELPHAPEX:
                return ElphapexHTTPClient(ip, alt_pwd=alt_pwd)
            case MinerType.GOLDSHELL:
                return GoldshellHTTPClient(ip, alt_pwd=alt_pwd)
            case MinerType.ICERIVER:
                return IceriverHTTPClient(ip, alt_pwd=alt_pwd)
            case MinerType.SEALMINER:
                return SealminerHTTPClient(ip, alt_pwd=alt_pwd)
            case MinerType.VOLCMINER:
                return VolcminerHTTPClient(ip, alt_pwd=alt_pwd)
            case MinerType.WHATSMINER:
                client = WhatsminerRPCClient(ip, alt_pwd=alt_pwd)
                return await self._upgrade_client(client, ip, alt_pwd)
            case MinerType.LUX_OS:
                return LuxminerRPCClient(ip, alt_pwd=alt_pwd)
            case MinerType.VNISH:
                return VnishHTTPClient(ip, alt_pwd=alt_pwd)
            case MinerType.AURADINE:
                return AuradineHTTPClient(ip, alt_pwd=alt_pwd)
            case MinerType.HIVEGPU:
                return SRBMinerHTTPClient(ip, alt_pwd=alt_pwd)
            case MinerType.IPOLLO:
                return IPolloHTTPClient(ip, alt_pwd=alt_pwd)
            case _:
                raise UnknownClientError(
                    f"unsupported client for IP {ip}: {miner_type.value}"
                )

    async def _upgrade_client(
        self, client: MinerClient, ip: str, alt_pwd: str | None = None
    ) -> MinerClient:
        """Probe for firmware variants that need a different backend."""
        try:
            # antminer: old firmware (<= 2020) uses the legacy endpoints
            if isinstance(client, AntminerHTTPClient):
                sys_info = await client.get_system_info()
                try:
                    if int(sys_info.system_filesystem_version[-4:]) <= 2020:
                        client.close()
                        return AntminerOldHTTPClient(ip, alt_pwd=alt_pwd)
                except ValueError:
                    return client
            # whatsminer: V3 firmware (> 202412) speaks the length-prefixed API
            if isinstance(client, WhatsminerRPCClient):
                version_info = await client.version()
                if int(version_info.fw_ver[:6]) > 202412:
                    client.close()
                    return WhatsminerTCPClient(ip, alt_pwd=alt_pwd)
        except _CLIENT_ERRORS as e:
            logger.error(f"{client.__repr__()} : client error raised: {e!s}")
        return client

    # -- high-level operations ---------------------------------------------

    async def get_miner_data(
        self, miner_type: MinerType, ip: str, alt_pwd: str | None = None
    ) -> MinerResult:
        """Fetch and parse standardized miner data for a single miner."""
        try:
            client = await self._make_client(miner_type, ip, alt_pwd)
        except UnknownClientError as e:
            return MinerResult(data=MinerData().as_dict(), error=e)
        try:
            data = await self._parse_miner_data(client)
            return MinerResult(data=data, error=client.error())
        finally:
            client.close()

    async def _parse_miner_data(self, client: MinerClient) -> dict[str, Any]:
        try:
            if isinstance(client, (AntminerHTTPClient, AntminerOldHTTPClient)):
                try:
                    log = await client.log()
                except _CLIENT_ERRORS as e:
                    logger.error(f"{client!r} : client error raised: {e!s}")
                    log = None
                models = AntminerModels(
                    system_info=await client.get_system_info(),
                    summary=await client.summary(),
                    pools=await client.pools(),
                    log=log,
                )
                return AntminerParser().parse(models).as_dict()

            if isinstance(client, ElphapexHTTPClient):
                models = ElphapexModels(
                    system_info=await client.get_system_info(),
                    summary=await client.summary(),
                    pools=await client.pools(),
                )
                return ElphapexParser().parse(models).as_dict()

            if isinstance(client, GoldshellHTTPClient):
                models = GoldshellModels(
                    system_info=await client.get_system_info(),
                    summary=await client.summary(),
                    miner_config=await client.get_miner_conf(),
                    algorithm=await client.get_algo(),
                    pools=await client.pools(),
                )
                return GoldshellParser().parse(models).as_dict()

            if isinstance(client, IceriverHTTPClient):
                models = IceriverModels(
                    summary=await client.summary(),
                    pools=await client.pools(),
                )
                return IceriverParser().parse(models).as_dict()

            if isinstance(client, SealminerHTTPClient):
                models = SealminerModels(
                    system_info=await client.get_system_info(),
                    summary=await client.summary(),
                    pools=await client.pools(),
                )
                return SealminerParser().parse(models).as_dict()

            if isinstance(client, VolcminerHTTPClient):
                models = VolcminerModels(
                    system_info=await client.get_system_info(),
                    summary=await client.summary(),
                    pools=await client.pools(),
                )
                return VolcminerParser().parse(models).as_dict()

            if isinstance(client, WhatsminerRPCClient):
                models = WhatsminerModels(
                    system_info=await client.get_system_info(),
                    summary=await client.summary(),
                    version_info=await client.version(),
                    pools=await client.pools(),
                    dev_details=await client.devdetails(),
                )
                return WhatsminerParser().parse(models).as_dict()

            if isinstance(client, WhatsminerTCPClient):
                models = WhatsminerV3Models(
                    device_info=await client.get_device_info(),
                    summary=await client.summary(),
                    pools=await client.pools(),
                )
                return WhatsminerV3Parser().parse(models).as_dict()

            if isinstance(client, LuxminerRPCClient):
                models = LuxminerModels(
                    system_info=await client.get_system_info(),
                    summary=await client.summary(),
                    version_info=await client.version(),
                    pools=await client.pools(),
                )
                return LuxminerParser().parse(models).as_dict()

            if isinstance(client, VnishHTTPClient):
                models = VnishModels(
                    system_info=await client.get_system_info(),
                    summary=await client.summary(),
                    pools=await client.pools(),
                )
                return VnishParser().parse(models).as_dict()

            if isinstance(client, AuradineHTTPClient):
                models = AuradineModels(
                    system_info=await client.get_system_info(),
                    summary=await client.summary(),
                    pools=await client.pools(),
                )
                return AuradineParser().parse(models).as_dict()

            if isinstance(client, SRBMinerHTTPClient):
                models = SRBMinerModels(
                    system_info=await client.get_system_info(),
                    pools=await client.pools(),
                )
                return SRBMinerParser().parse(models).as_dict()

            if isinstance(client, IPolloHTTPClient):
                models = IPolloModels(
                    system_info=await client.get_system_info(),
                    summary=await client.summary(),
                    pools=await client.pools(),
                    network_info=await client.get_network_info(),
                )
                return IPolloParser().parse(models).as_dict()
        except _CLIENT_ERRORS as e:
            logger.error(f"{client!r} : client error raised: {e!s}")
            client.close(e)

        return MinerData().as_dict()

    async def get_miner_pool_conf(
        self, miner_type: MinerType, ip: str, alt_pwd: str | None = None
    ) -> MinerResult:
        """Return the miner's pool configuration padded to 3 slots."""
        conf = PoolConf()
        try:
            client = await self._make_client(miner_type, ip, alt_pwd)
        except UnknownClientError as e:
            return MinerResult(data=conf, error=e)
        error: Exception | None = None
        try:
            pool_conf = await client.get_pool_conf()
        except _CLIENT_ERRORS as e:
            logger.error(f"{client!r} : client error raised: {e!s}")
            error = e
        else:
            for pool in pool_conf.root:
                conf.urls.append(pool.url)
                conf.users.append(pool.user)
                conf.passwds.append(pool.pwd)
        finally:
            client.close()
        while len(conf.urls) < 3:
            conf.urls.append("")
            conf.users.append("")
            conf.passwds.append("")
        return MinerResult(data=conf, error=error)

    async def update_miner_pools(
        self,
        miner_type: MinerType,
        ip: str,
        urls: list[str],
        users: list[str],
        passwds: list[str],
        alt_pwd: str | None = None,
    ) -> MinerResult:
        """Update the miner's pool configuration."""
        try:
            client = await self._make_client(miner_type, ip, alt_pwd)
        except UnknownClientError as e:
            return MinerResult(error=e)
        try:
            data = await client.update_pool_conf(urls, users, passwds)
            return MinerResult(data=data)
        except _CLIENT_ERRORS as e:
            logger.error(f"{client.__repr__()} : client error raised: {e!s}")
            return MinerResult(error=e)
        finally:
            client.close()

    async def _control_miner(
        self,
        action: ControlAction,
        miner_type: MinerType,
        ip: str,
        alt_pwd: str | None = None,
    ) -> MinerResult:
        """Run a control action using an operation-scoped miner client."""
        try:
            client = await self._make_client(miner_type, ip, alt_pwd)
        except UnknownClientError as e:
            return MinerResult(error=e)
        try:
            match action:
                case "start":
                    data = await client.start()
                case "stop":
                    data = await client.stop()
                case "restart":
                    data = await client.restart()
                case "reboot":
                    data = await client.reboot()
            return MinerResult(data=data)
        except _CLIENT_ERRORS as e:
            logger.error(f"{client!r} : client error raised: {e!s}")
            return MinerResult(error=e)
        finally:
            client.close()

    async def start_miner(
        self, miner_type: MinerType, ip: str, alt_pwd: str | None = None
    ) -> MinerResult:
        """Start mining on a single miner."""
        return await self._control_miner("start", miner_type, ip, alt_pwd)

    async def stop_miner(
        self, miner_type: MinerType, ip: str, alt_pwd: str | None = None
    ) -> MinerResult:
        """Stop mining on a single miner."""
        return await self._control_miner("stop", miner_type, ip, alt_pwd)

    async def restart_miner(
        self, miner_type: MinerType, ip: str, alt_pwd: str | None = None
    ) -> MinerResult:
        """Restart mining on a single miner."""
        return await self._control_miner("restart", miner_type, ip, alt_pwd)

    async def reboot_miner(
        self, miner_type: MinerType, ip: str, alt_pwd: str | None = None
    ) -> MinerResult:
        """Reboot a single miner."""
        return await self._control_miner("reboot", miner_type, ip, alt_pwd)

    async def update_miner_passwd(
        self,
        miner_type: MinerType,
        ip: str,
        alt_pwd: str | None = None,
        old_passwd: str | None = None,
        new_passwd: str | None = None,
    ) -> MinerResult:
        """Update the miner's password."""
        if old_passwd is None or new_passwd is None:
            return MinerResult(error=APIError("Old and new passwords are required"))
        try:
            client = await self._make_client(miner_type, ip, alt_pwd)
        except UnknownClientError as e:
            return MinerResult(error=e)
        try:
            data = await client.update_passwd(old_passwd, new_passwd)
            return MinerResult(data=data)
        except _CLIENT_ERRORS as e:
            logger.error(f"{client.__repr__()} : client error raised: {e!s}")
            return MinerResult(error=e)
        finally:
            client.close()

    async def locate_miner(
        self,
        miner_type: MinerType,
        ip: str,
        alt_pwd: str | None = None,
        duration_ms: int | None = None,
    ) -> MinerResult:
        """Blink the miner's LEDs for a set duration to physically locate it.

        Cancelling the awaiting task stops the blink early (the LEDs are turned
        back off in the finally block).
        """
        if duration_ms is None:
            duration_ms = int(get_setting("locate_duration_ms", 10000))
        try:
            client = await self._make_client(miner_type, ip, alt_pwd)
        except UnknownClientError as e:
            return MinerResult(error=e)
        try:
            _ = await client.blink(enabled=True)
            try:
                await asyncio.sleep(duration_ms / 1000)
            finally:
                try:
                    _ = await client.blink(enabled=False)
                except _CLIENT_ERRORS:
                    pass
        except _CLIENT_ERRORS as e:
            logger.error(f"{client.__repr__()} : client error raised: {e!s}")
            return MinerResult(error=e)
        finally:
            client.close()
        return MinerResult()
