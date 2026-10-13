# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from mod.ipr_asic.rpc.cgminer import CGMinerRPCClient


class IBeLinkRPCClient(CGMinerRPCClient):
    """CGMiner RPC client for iBeLink miners"""

    def __init__(self, ip: str, port: int = 4029, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)
