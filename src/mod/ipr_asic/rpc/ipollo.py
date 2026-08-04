# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE


from .cgminer import CGMinerRPCClient


class IPolloRPCClient(CGMinerRPCClient):
    """Abstraction class for IPollo/cgminer 4.10.0"""

    def __init__(self, ip: str, port: int = 4028, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)
