# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import httpx
from PySide6.QtCore import QObject

from mod.ipr_asic import settings
from mod.ipr_asic.data import BaseParser, MinerData, MinerType
from mod.ipr_asic.data.miners import (
    AntminerParser,
    AuradineParser,
    ElphapexParser,
    GoldshellParser,
    IceriverParser,
    LuxminerParser,
    SealminerParser,
    SRBMinerParser,
    VnishParser,
    VolcminerParser,
    WhatsminerParser,
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
    SealminerHTTPClient,
    SRBMinerHTTPClient,
    VnishHTTPClient,
    VolcminerHTTPClient,
)
from mod.ipr_asic.protocol import BaseClient
from mod.ipr_asic.rpc import (
    LuxminerRPCClient,
    WhatsminerRPCClient,
    WhatsminerTCPClient,
)
from mod.lm.ipreport import MinerTypeHint

logger = logging.getLogger(__name__)

# client errors that a high-level operation may recover from / report
_CLIENT_ERRORS = (
    FailedConnectionError,
    AuthenticationError,
    APIError,
    OSError,
    LookupError,
    NotImplementedError,
)


@dataclass
class MinerResult:
    """Result of a high-level facade operation.

    Carries the operation payload and any client error that occurred, replacing
    the apiv2 ``client_error()``-after-the-fact pattern (which relied on a single
    shared active client and is unsafe under concurrent/bulk operations).
    """

    data: Any = None
    error: Exception | None = None

    @property
    def ok(self) -> bool:
        return self.error is None


@dataclass
class PoolConf:
    urls: list[str] = field(default_factory=list)
    users: list[str] = field(default_factory=list)
    passwds: list[str] = field(default_factory=list)


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
        self._parent = parent

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
                miner_type = await self._parse_http_type(ip)
                if miner_type is None:
                    return MinerType.UNKNOWN
                if miner_type == MinerType.HAMMER:
                    model = await self._get_volcminer_model(ip)
                    if model is None:
                        return MinerType.HAMMER
                    if "HAMMER" not in model.upper():
                        return MinerType.VOLCMINER
                    return MinerType.HAMMER
                return miner_type
            case _:
                return MinerType.UNKNOWN

    async def _parse_http_type(self, ip: str) -> MinerType | None:
        url = f"http://{ip}/"
        timeout = settings.get("api_function_timeout", 5)
        try:
            async with httpx.AsyncClient(timeout=timeout) as c:
                resp = await c.get(url, follow_redirects=True)
        except httpx.HTTPError:
            return None
        www_auth = resp.headers.get("www-authenticate", "")
        if resp.status_code == 401 and 'realm="antMiner' in www_auth:
            return MinerType.ANTMINER
        if resp.status_code == 401 and 'realm="blackMiner' in www_auth:
            return MinerType.HAMMER
        if "Luxor Firmware" in resp.text:
            return MinerType.LUX_OS
        if "AnthillOS" in resp.text:
            return MinerType.VNISH
        return None

    async def _get_volcminer_model(self, ip: str) -> str | None:
        client = VolcminerHTTPClient(ip)
        try:
            system_info = await client.get_system_info()
        except _CLIENT_ERRORS:
            return None
        finally:
            client._close()
        try:
            return system_info["minertype"]
        except (TypeError, LookupError):
            return None

    # -- client creation ----------------------------------------------------

    async def _make_client(
        self, miner_type: MinerType, ip: str, alt_pwd: str | None = None
    ) -> BaseClient:
        match miner_type:
            case MinerType.ANTMINER:
                client: BaseClient = AntminerHTTPClient(ip, alt_pwd=alt_pwd)
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
            case _:
                raise UnknownClientError(
                    f"unsupported client for IP {ip}: {miner_type.value}"
                )

    async def _upgrade_client(
        self, client: BaseClient, ip: str, alt_pwd: str | None = None
    ) -> BaseClient:
        """Probe for firmware variants that need a different backend."""
        try:
            # antminer: old firmware (<= 2020) uses the legacy endpoints
            if isinstance(client, AntminerHTTPClient):
                sys_info = await client.get_system_info()
                try:
                    if int(sys_info["system_filesystem_version"][-4:]) <= 2020:
                        client._close()
                        return AntminerOldHTTPClient(ip, alt_pwd=alt_pwd)
                except ValueError:
                    return client
            # whatsminer: V3 firmware (> 202412) speaks the length-prefixed API
            if isinstance(client, WhatsminerRPCClient):
                version_info = await client.version()
                if int(version_info["fw_ver"][:6]) > 202412:
                    client._close()
                    return WhatsminerTCPClient(ip, alt_pwd=alt_pwd)
        except (APIError, FailedConnectionError, LookupError, OSError) as e:
            logger.error(f"{client.__repr__()} : client error raised: {str(e)}")
        return client

    def _parser_for(self, client: BaseClient) -> BaseParser | None:
        if isinstance(client, (AntminerHTTPClient, AntminerOldHTTPClient)):
            return AntminerParser()
        if isinstance(client, VnishHTTPClient):
            return VnishParser()
        if isinstance(client, ElphapexHTTPClient):
            return ElphapexParser()
        if isinstance(client, GoldshellHTTPClient):
            return GoldshellParser()
        if isinstance(client, IceriverHTTPClient):
            return IceriverParser()
        if isinstance(client, SealminerHTTPClient):
            return SealminerParser()
        if isinstance(client, VolcminerHTTPClient):
            return VolcminerParser()
        if isinstance(client, WhatsminerTCPClient):
            return WhatsminerV3Parser()
        if isinstance(client, WhatsminerRPCClient):
            return WhatsminerParser()
        if isinstance(client, LuxminerRPCClient):
            return LuxminerParser()
        if isinstance(client, AuradineHTTPClient):
            return AuradineParser()
        if isinstance(client, SRBMinerHTTPClient):
            return SRBMinerParser()
        return None

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
            client._close()

    async def _parse_miner_data(self, client: BaseClient) -> dict[str, Any]:
        parser = self._parser_for(client)
        if parser is None:
            return MinerData().as_dict()
        try:
            system_info = await client.get_system_info()
            summary = await client.summary()
            if isinstance(parser, AntminerParser):
                parser.parse_summary(summary)
                system_log = await client.log()
                parser.parse_platform(system_log)
                parser.parse_system_info(system_info)
            elif isinstance(parser, SRBMinerParser):
                parser.parse_all(system_info)
                # uptime is not part of the generic parse_all() sequence.
                parser.parse_summary(system_info)
            elif isinstance(parser, GoldshellParser):
                parser.parse_system_info(system_info)
                miner_conf = await client.get_miner_conf()
                parser.parse_mac(miner_conf)
                algo_info = await client.get_algo()
                parser.parse_algorithm(algo_info)
            elif isinstance(parser, WhatsminerParser):
                parser.parse_summary(summary)
                parser.parse_system_info(system_info)
                devs = await client.devdetails()
                parser.parse_subtype(devs)
                version_info = await client.version()
                parser.parse_version_info(version_info)
            elif isinstance(parser, LuxminerParser):
                parser.parse_summary(summary)
                parser.parse_system_info(system_info)
                version_info = await client.version()
                parser.parse_version_info(version_info)
            else:
                parser.parse_summary(summary)
                parser.parse_all(system_info)
            try:
                pools = await client.pools()
            except _CLIENT_ERRORS as e:
                logger.error(f"{client.__repr__()} : client error raised: {str(e)}")
                pools = []
            parser.parse_pools(pools)
        except _CLIENT_ERRORS as e:
            logger.error(f"{client.__repr__()} : client error raised: {str(e)}")
            client._close(e)
        return parser.get_data()

    async def get_miner_pool_conf(
        self, miner_type: MinerType, ip: str, alt_pwd: str | None = None
    ) -> MinerResult:
        """Return the miner's pool configuration padded to 3 slots."""
        conf = PoolConf()
        try:
            client = await self._make_client(miner_type, ip, alt_pwd)
        except UnknownClientError as e:
            return MinerResult(data=conf, error=e)
        pool_conf: list[dict] = []
        error: Exception | None = None
        try:
            pool_conf = await client.get_pool_conf()
        except _CLIENT_ERRORS as e:
            logger.error(f"{client.__repr__()} : client error raised: {str(e)}")
            error = e
        finally:
            client._close()

        for pool in pool_conf:
            conf.urls.append(pool["addr"] if "addr" in pool else pool["url"])
            conf.users.append(pool["user"])
            conf.passwds.append(pool["pass"])
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
            logger.error(f"{client.__repr__()} : client error raised: {str(e)}")
            return MinerResult(error=e)
        finally:
            client._close()

    async def _control_miner(
        self,
        action: str,
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
            operation = getattr(client, action, None)
            if operation is None:
                raise NotImplementedError(
                    f"{action.capitalize()} is not supported for {miner_type.value}"
                )
            data = await operation()
            return MinerResult(data=data)
        except _CLIENT_ERRORS as e:
            logger.error(f"{client.__repr__()} : client error raised: {str(e)}")
            return MinerResult(error=e)
        finally:
            client._close()

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
            duration_ms = settings.get("locate_duration_ms", 10000)
        try:
            client = await self._make_client(miner_type, ip, alt_pwd)
        except UnknownClientError as e:
            return MinerResult(error=e)
        try:
            await client.blink(enabled=True)
            try:
                await asyncio.sleep(duration_ms / 1000)
            finally:
                try:
                    await client.blink(enabled=False)
                except _CLIENT_ERRORS:
                    pass
        except _CLIENT_ERRORS as e:
            logger.error(f"{client.__repr__()} : client error raised: {str(e)}")
            return MinerResult(error=e)
        finally:
            client._close()
        return MinerResult()
