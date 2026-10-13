# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from mod.ipr_asic.rpc.cgminer import CGMinerRPCClient


class GCMinerRPCClient(CGMinerRPCClient):
    """Abstraction class for GCMiner/IPollo"""
