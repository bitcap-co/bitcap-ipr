# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from .antminer import AntminerParser
from .auradine import AuradineParser
from .elphapex import ElphapexParser
from .goldshell import GoldshellParser
from .iceriver import IceriverParser
from .luxminer import LuxminerParser
from .sealminer import SealminerParser
from .srbminer import SRBMinerParser
from .vnish import VnishParser
from .volcminer import VolcminerParser
from .whatsminer import WhatsminerParser, WhatsminerV3Parser

__all__ = [
    "AntminerParser",
    "AuradineParser",
    "ElphapexParser",
    "GoldshellParser",
    "IceriverParser",
    "LuxminerParser",
    "SRBMinerParser",
    "SealminerParser",
    "VnishParser",
    "VolcminerParser",
    "WhatsminerParser",
    "WhatsminerV3Parser",
]
