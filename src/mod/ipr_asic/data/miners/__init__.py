# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from .antminer import AntminerModels, AntminerParser
from .auradine import AuradineModels, AuradineParser
from .elphapex import ElphapexModels, ElphapexParser
from .goldshell import GoldshellModels, GoldshellParser
from .iceriver import IceriverModels, IceriverParser
from .ipollo import IPolloModels, IPolloParser
from .luxminer import LuxminerModels, LuxminerParser
from .sealminer import SealminerModels, SealminerParser
from .srbminer import SRBMinerModels, SRBMinerParser
from .vnish import VnishModels, VnishParser
from .volcminer import VolcminerModels, VolcminerParser
from .whatsminer import (
    WhatsminerModels,
    WhatsminerParser,
    WhatsminerV3Models,
    WhatsminerV3Parser,
)

__all__ = [
    "AntminerModels",
    "AntminerParser",
    "AuradineModels",
    "AuradineParser",
    "ElphapexModels",
    "ElphapexParser",
    "GoldshellModels",
    "GoldshellParser",
    "IPolloModels",
    "IPolloParser",
    "IceriverModels",
    "IceriverParser",
    "LuxminerModels",
    "LuxminerParser",
    "SRBMinerModels",
    "SRBMinerParser",
    "SealminerModels",
    "SealminerParser",
    "VnishModels",
    "VnishParser",
    "VolcminerModels",
    "VolcminerParser",
    "WhatsminerModels",
    "WhatsminerParser",
    "WhatsminerV3Models",
    "WhatsminerV3Parser",
]
