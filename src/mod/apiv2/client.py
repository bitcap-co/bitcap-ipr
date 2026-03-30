import logging
from typing import Any

import requests
from PySide6.QtCore import QObject, QTimer

from mod.lm.ipreport import MinerTypeHint

from .base import BaseHTTPClient, BaseRPCClient, BaseTCPClient
from .data import MinerData, MinerType
from .data.miners import (
    AntminerParser,
    BaseParser,
    ElphapexParser,
    GoldshellParser,
    IceriverParser,
    LuxminerParser,
    SealminerParser,
    VnishParser,
    VolcminerParser,
    WhatsminerParser,
    WhatsminerV3Parser,
)
from .errors import APIError, AuthenticationError, FailedConnectionError
from .http import (
    AntminerHTTPClient,
    ElphapexHTTPClient,
    GoldshellHTTPClient,
    IceriverHTTPClient,
    SealminerHTTPClient,
    VnishHTTPClient,
    VolcminerHTTPClient,
)
from .rpc import (
    CGMinerRPCClient,
    LuxminerRPCClient,
    WhatsminerRPCClient,
    WhatsminerTCPClient,
)

logger = logging.getLogger(__name__)


class ASICClient(QObject):
    """
    ASICClient is the main interface for interacting with various miner backends/APIs

    Args:
        parent (QObject) : parent object
    """

    def __init__(self, parent: QObject) -> None:
        super().__init__(parent)
        self._parent = parent
        self._locate_timer: QTimer | None = None

        self.client: BaseHTTPClient | BaseRPCClient | BaseTCPClient | None = None

    def __repr__(self) -> str:
        if self.client is not None:
            return f"{self.__class__.__name__}[{self.client.__repr__()}]"
        return f"{self.__class__.__name__}"

    def _set_active_client(
        self, client: BaseHTTPClient | BaseRPCClient | BaseTCPClient
    ):
        self.close_client()
        self.client = client

    def create_antminer_client(self, ip: str, alt_pwd: str | None = None) -> None:
        self._set_active_client(AntminerHTTPClient(ip, alt_pwd=alt_pwd))

    def create_elphapex_client(self, ip: str, alt_pwd: str | None = None) -> None:
        self._set_active_client(ElphapexHTTPClient(ip, alt_pwd=alt_pwd))

    def create_goldshell_client(self, ip: str, alt_pwd: str | None = None) -> None:
        self._set_active_client(GoldshellHTTPClient(ip, alt_pwd=alt_pwd))

    def create_iceriver_client(self, ip: str, alt_pwd: str | None = None) -> None:
        self._set_active_client(IceriverHTTPClient(ip, alt_pwd=alt_pwd))

    def create_sealminer_client(self, ip: str, alt_pwd: str | None = None) -> None:
        self._set_active_client(SealminerHTTPClient(ip, alt_pwd=alt_pwd))

    def create_volcminer_client(self, ip: str, alt_pwd: str | None = None) -> None:
        self._set_active_client(VolcminerHTTPClient(ip, alt_pwd=alt_pwd))

    def create_whatsminer_client(self, ip: str, alt_pwd: str | None = None) -> None:
        self._set_active_client(WhatsminerRPCClient(ip, alt_pwd=alt_pwd))

    def create_whatsminerV3_client(self, ip: str, alt_pwd: str | None = None) -> None:
        self._set_active_client(WhatsminerTCPClient(ip, alt_pwd=alt_pwd))

    def create_cgminer_client(self, ip: str, alt_pwd: str | None = None) -> None:
        self._set_active_client(CGMinerRPCClient(ip, alt_pwd=alt_pwd))

    def create_vnish_client(self, ip: str, alt_pwd: str | None = None) -> None:
        self._set_active_client(VnishHTTPClient(ip, alt_pwd=alt_pwd))

    def create_luxos_client(self, ip: str, alt_pwd: str | None = None) -> None:
        self._set_active_client(LuxminerRPCClient(ip, alt_pwd=alt_pwd))

    def create_client(
        self, miner_type: MinerType, ip: str, alt_pwd: str | None = None
    ) -> None:
        match miner_type:
            case MinerType.ANTMINER:
                self.create_antminer_client(ip, alt_pwd=alt_pwd)
            case MinerType.ELPHAPEX:
                self.create_elphapex_client(ip, alt_pwd=alt_pwd)
            case MinerType.GOLDSHELL:
                self.create_goldshell_client(ip, alt_pwd=alt_pwd)
            case MinerType.ICERIVER:
                self.create_antminer_client(ip, alt_pwd=alt_pwd)
            case MinerType.SEALMINER:
                self.create_sealminer_client(ip, alt_pwd=alt_pwd)
            case MinerType.VOLCMINER:
                self.create_volcminer_client(ip, alt_pwd=alt_pwd)
            case MinerType.WHATSMINER:
                self.create_whatsminer_client(ip, alt_pwd=alt_pwd)
                # upgrade to v3
                self._btminerV3_upgrade(ip, alt_pwd=alt_pwd)
            case MinerType.LUX_OS:
                self.create_luxos_client(ip, alt_pwd=alt_pwd)
            case MinerType.VNISH:
                self.create_vnish_client(ip, alt_pwd=alt_pwd)
            case _:
                # type is unknown or not supported
                self.client = None
                return

    def identify(self, miner_hint: MinerTypeHint, ip: str) -> MinerType:
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
            case MinerTypeHint.COMMON:
                miner_type = self._parse_http_type(ip)
                if miner_type is None:
                    return MinerType.UNKNOWN
                else:
                    if miner_type == MinerType.HAMMER:
                        model = self._get_volcminer_model(ip)
                        if model is None:
                            return MinerType.HAMMER
                        if "HAMMER" not in model.upper():
                            return MinerType.VOLCMINER
                        return MinerType.HAMMER
                    return miner_type
            case _:
                return MinerType.UNKNOWN

    def get_miner_data(self) -> dict[str, Any]:
        if isinstance(self.client, AntminerHTTPClient):
            return self._parse_miner_data(AntminerParser())
        elif isinstance(self.client, VnishHTTPClient):
            return self._parse_miner_data(VnishParser())
        elif isinstance(self.client, ElphapexHTTPClient):
            return self._parse_miner_data(ElphapexParser())
        elif isinstance(self.client, GoldshellHTTPClient):
            return self._parse_miner_data(GoldshellParser())
        elif isinstance(self.client, IceriverHTTPClient):
            return self._parse_miner_data(IceriverParser())
        elif isinstance(self.client, SealminerHTTPClient):
            return self._parse_miner_data(SealminerParser())
        elif isinstance(self.client, VolcminerHTTPClient):
            return self._parse_miner_data(VolcminerParser())
        elif isinstance(self.client, WhatsminerTCPClient):
            return self._parse_miner_data(WhatsminerV3Parser())
        elif isinstance(self.client, WhatsminerRPCClient):
            return self._parse_miner_data(WhatsminerParser())
        elif isinstance(self.client, LuxminerRPCClient):
            return self._parse_miner_data(LuxminerParser())
        return MinerData().as_dict()

    def _parse_miner_data(self, parser: BaseParser) -> dict[str, Any]:
        if not self.client:
            return parser.get_data()
        try:
            system_info = self.client.get_system_info()
            if isinstance(parser, AntminerParser):
                system_log = self.client.log()
                parser.parse_platform(system_log)
                parser.parse_system_info(system_info)
            elif (
                isinstance(parser, IceriverParser)
                or isinstance(parser, VolcminerParser)
                or isinstance(parser, SealminerParser)
                or isinstance(parser, WhatsminerV3Parser)
                or isinstance(parser, ElphapexParser)
                or isinstance(parser, VnishParser)
            ):
                parser.parse_all(system_info)
            elif isinstance(parser, GoldshellParser):
                parser.parse_system_info(system_info)
                algo_info = self.client.get_algo()
                parser.parse_algorithm(algo_info)
            elif isinstance(parser, WhatsminerParser):
                parser.parse_system_info(system_info)
                devs = self.client.devdetails()
                parser.parse_subtype(devs)
                version_info = self.client.version()
                parser.parse_version_info(version_info)
            elif isinstance(parser, LuxminerParser):
                parser.parse_system_info(system_info)
                version_info = self.client.version()
                parser.parse_version_info(version_info)
            try:
                pools = self.client.pools()
            except (AuthenticationError, APIError, FailedConnectionError, OSError) as e:
                logger.error(
                    f"{self.client.__repr__()} : client error raised: {str(e)}"
                )
                pools: list[dict] = []
            parser.parse_pools(pools)
        except (FailedConnectionError, AuthenticationError, APIError, OSError) as e:
            logger.error(f"{self.client.__repr__()} : client error raised: {str(e)}")
            self.close_client(ex=e)
        return parser.get_data()

    def _parse_http_type(self, ip: str) -> MinerType | None:
        url = f"http://{ip}/"
        with requests.Session() as s:
            try:
                resp = s.get(url, allow_redirects=True)
            except (requests.HTTPError, requests.Timeout, requests.ConnectionError):
                pass
            else:
                if resp.status_code == 401 and 'realm="antMiner' in resp.headers.get(
                    "www-authenticate", ""
                ):
                    return MinerType.ANTMINER
                if resp.status_code == 401 and 'realm="blackMiner' in resp.headers.get(
                    "www-authenticate", ""
                ):
                    return MinerType.HAMMER
                if "Luxor Firmware" in resp.text:
                    return MinerType.LUX_OS
                if "AnthillOS" in resp.text:
                    return MinerType.VNISH
        return None

    def _get_volcminer_model(self, ip: str) -> str | None:
        client = VolcminerHTTPClient(ip)
        try:
            system_info = client.get_system_info()
        except (FailedConnectionError, AuthenticationError, APIError):
            #
            return None
        else:
            try:
                miner_model = system_info["minertype"]
                return miner_model
            except (TypeError, LookupError):
                pass
            return None

    def _btminerV3_upgrade(self, ip: str, alt_pwd: str | None = None) -> None:
        if self.client and isinstance(self.client, WhatsminerRPCClient):
            try:
                version_info = self.client.version()
                if int(version_info["fw_ver"][:6]) > 202412:
                    self.create_whatsminerV3_client(ip, alt_pwd=alt_pwd)
            except (APIError, FailedConnectionError, OSError):
                #
                pass

    def close_client(self, ex: Exception | None = None) -> None:
        if self.client is not None:
            logger.info(f"{self.__repr__()} : close client.")
            self.client._close(ex)
            self.client = None
