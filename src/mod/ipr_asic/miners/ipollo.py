# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from mod.ipr_asic.http import IPolloHTTPClient
from mod.ipr_asic.protocol import BaseHTTPClient, BaseRPCClient
from mod.ipr_asic.rpc import CGMinerRPCClient

from .base import BaseMiner


class IPolloMiner(BaseMiner):
    """iPollo miner backend composed from its HTTP and CGMiner APIs.

    The HTTP API exposes iPollo-specific system and miner data, while the RPC
    API provides the standard CGMiner command set inherited from ``BaseMiner``.
    Either client may be injected for tests or firmware-specific variants.
    """

    HTTP_COMMANDS = ("get_system_info", "summary", "pools")

    def __init__(
        self,
        ip: str,
        *,
        alt_pwd: str | None = None,
        http_port: int = 80,
        rpc_port: int = 4028,
        http: BaseHTTPClient | None = None,
        rpc: BaseRPCClient | None = None,
    ) -> None:
        if http is None:
            http = IPolloHTTPClient(ip, port=http_port, alt_pwd=alt_pwd)
        if rpc is None:
            rpc = CGMinerRPCClient(ip, port=rpc_port, alt_pwd=alt_pwd)
        super().__init__(ip, http=http, rpc=rpc)
