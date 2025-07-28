import logging
from typing import Dict, Optional

from PySide6.QtCore import (
    QObject,
    QTimer,
)

from mod.api import settings
from mod.api.errors import (
    AuthenticationError,
    FailedConnectionError,
)
from mod.api.parser import Parser

from .miners.bitmain import BitmainHTTPClient, BitmainParser
from .miners.dragonball import DragonballHTTPClient, DragonballParser
from .miners.elphapex import ElphapexHTTPClient, ElphapexParser
from .miners.goldshell import GoldshellHTTPClient, GoldshellParser
from .miners.iceriver import IceriverHTTPClient, IceriverParser
from .miners.sealminer import SealminerHTTPClient, SealminerParser
from .miners.volcminer import VolcminerHTTPClient, VolcminerParser
from .miners.whatsminer import WhatsminerParser, WhatsminerRPCClient
from .miners.whatsminer.v3 import WhatsminerV3Client, WhatsminerV3Parser

logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self, parent: QObject):
        self.parent = parent
        self.client = None
        self.locate: Optional[QTimer] = None
        self.target_info: Dict[str, str] = {
            "serial": "N/A",
            "subtype": "N/A",
            "algorithm": "N/A",
            "firmware": "N/A",
            "platform": "N/A",
        }

    def get_client(self):
        return self.client

    def create_bitmain_client(
        self, ip_addr: str, passwd: Optional[str] = None, vnish_passwd: Optional[str] = None
    ) -> None:
        try:
            self.client = BitmainHTTPClient(ip_addr, passwd, vnish_passwd)
        except (FailedConnectionError, AuthenticationError) as err:
            logger.error(err)

    def create_iceriver_client(
        self, ip_addr: str, passwd: Optional[str] = None, pb_key: Optional[str] = None
    ) -> None:
        try:
            self.client = IceriverHTTPClient(ip_addr, passwd, pb_key)
        except FailedConnectionError as err:
            logger.error(err)

    def create_whatsminer_client(self, ip_addr: str, passwd: Optional[str] = None) -> None:
        try:
            self.client = WhatsminerRPCClient(ip_addr, passwd)
        except FailedConnectionError as err:
            logger.error(err)

    def create_whatsminerv3_client(self, ip_addr: str, user: Optional[str] = None, passwd: Optional[str] = None) -> None:
        try:
            self.client = WhatsminerV3Client(ip_addr, user, passwd)
        except FailedConnectionError as err:
            logger.error(err)

    def create_volcminer_client(self, ip_addr: str, passwd: Optional[str] = None) -> None:
        try:
            self.client = VolcminerHTTPClient(ip_addr, passwd)
        except (FailedConnectionError, AuthenticationError) as err:
            logger.error(err)

    def create_goldshell_client(self, ip_addr: str, passwd: Optional[str] = None) -> None:
        try:
            self.client = GoldshellHTTPClient(ip_addr, passwd)
        except (FailedConnectionError, AuthenticationError) as err:
            logger.error(err)

    def create_sealminer_client(self, ip_addr: str, passwd: Optional[str] = None) -> None:
        try:
            self.client = SealminerHTTPClient(ip_addr, passwd)
        except (FailedConnectionError, AuthenticationError) as err:
            logger.error(err)

    def create_elphapex_client(self, ip_addr: str, passwd: Optional[str] = None) -> None:
        try:
            self.client = ElphapexHTTPClient(ip_addr, passwd)
        except (FailedConnectionError, AuthenticationError) as err:
            logger.error(err)

    def create_dragonball_client(self, ip_addr: str, passwd: Optional[str] = None) -> None:
        try:
            self.client = DragonballHTTPClient(ip_addr, passwd)
        except (FailedConnectionError, AuthenticationError) as err:
            logger.error(err)

    def create_client_from_type(
        self, miner_type: str, ip_addr: str, auth: Optional[str] =  None, custom_auth: Optional[str] = None
    ) -> None:
        match miner_type:
            case "antminer":
                self.create_bitmain_client(ip_addr, auth, custom_auth)
            case "iceriver":
                self.create_iceriver_client(ip_addr, auth, custom_auth)
            case "whatsminer":
                self.create_whatsminer_client(ip_addr, auth)
                self.upgrade_whatsminer_client(ip_addr)
            case "volcminer":
                self.create_volcminer_client(ip_addr, auth)
            case "goldshell":
                self.create_goldshell_client(ip_addr, auth)
            case "sealminer":
                self.create_sealminer_client(ip_addr, auth)
            case "elphapex":
                self.create_elphapex_client(ip_addr, auth)
            case "dragonball":
                self.create_dragonball_client(ip_addr, auth)
            case _:
                return

    def locate_miner(self, miner_type: str) -> None:
        self.locate = QTimer(self.parent)
        self.locate.setSingleShot(True)
        self.locate.timeout.connect(self.stop_locate)
        duration = settings.get("locate_duration_ms")
        logger.info(f" locate miner for {duration}ms.")
        match miner_type:
            case "antminer" | "whatsminer":
                try:
                    self.client.blink(enabled=True)
                    self.locate.start(duration)
                except AuthenticationError as err:
                    logger.error(err)
                    self.close_client()
            case "iceriver" | "volcminer" | "goldshell" | "sealminer" | "elphapex":
                self.client.blink(enabled=True)
                self.locate.start(duration)

    def stop_locate(self) -> None:
        self.client.blink(enabled=False)
        self.close_client()

    def get_missing_mac_addr(self) -> Optional[str]:
        if isinstance(self.client, IceriverHTTPClient) or isinstance(
            self.client, ElphapexHTTPClient
        ):
            mac = self.client.get_mac_addr()
            if mac:
                return mac
            else:
                return "Failed"

    def get_common_miner_type(self):
        if self.client:
            system_info = self.client.get_system_info()
            for k in system_info.keys():
                if k in ["miner", "minertype"]:
                    return system_info[k].strip().lower()

    def is_antminer(self) -> bool:
        miner_type: str = self.get_common_miner_type()
        if miner_type and miner_type.__contains__("antminer"):
            return True
        return False

    def is_volcminer(self) -> bool:
        miner_type = self.get_common_miner_type()
        if miner_type and miner_type.__contains__("volcminer"):
            return True
        return False

    def is_dragonball(self) -> bool:
        miner_type = self.get_common_miner_type()
        if miner_type and miner_type == "miner":
            return True
        return False

    def upgrade_whatsminer_client(self, ip: str, user: Optional[str] = None, passwd: Optional[str] = None) -> None:
        if self.client and isinstance(self.client, WhatsminerRPCClient):
            ver = self.client.get_version()
            if int(ver["Msg"]["fw_ver"][:6]) > 202412:
                    self.close_client()
                    self.create_whatsminerv3_client(ip, user, passwd)

    def get_target_info(self, parser: Parser) -> Dict[str, str]:
        result = parser.get_target()
        if not self.client:
            for k in result.keys():
                result[k] = "Failed"
            return result
        sys = self.client.get_system_info()
        if isinstance(parser, BitmainParser):
            if not self.client.is_custom:
                log = self.client.get_bitmain_system_log()
                parser.parse_platform(log)
            else:
                parser.parse_platform(sys)
            parser.parse_system_info(sys)
        elif (
            isinstance(parser, IceriverParser)
            or isinstance(parser, VolcminerParser)
            or isinstance(parser, SealminerParser)
        ):
            parser.parse_all(sys)
        elif isinstance(parser, GoldshellParser):
            parser.parse_system_info(sys)
            algo = self.client.get_algo_settings()
            parser.parse_algorithm(algo)
        elif isinstance(parser, WhatsminerParser):
            parser.parse_system_info(sys)
            devs = self.client.get_dev_details()
            parser.parse_subtype(devs)
            ver = self.client.get_version()
            parser.parse_version_info(ver)
        elif isinstance(parser, WhatsminerV3Parser):
            parser.parse_system_info(sys)
            dev = self.client.get_miner_info()
            parser.parse_miner_info(dev)
        elif isinstance(parser, ElphapexParser):
            parser.parse_system_info(sys)
            info = self.client.get_miner_info()
            parser.parse_platform(info)
        elif isinstance(parser, DragonballParser):
            parser.parse_system_info(sys)
        return parser.get_target()

    def get_target_data_from_type(self, miner_type: str) -> Dict[str, str]:
        match miner_type:
            case "antminer":
                return self.get_target_info(BitmainParser(self.target_info))
            case "iceriver":
                return self.get_target_info(IceriverParser(self.target_info))
            case "whatsminer":
                if isinstance(self.client, WhatsminerV3Client):
                    return self.get_target_info(WhatsminerV3Parser(self.target_info))
                return self.get_target_info(WhatsminerParser(self.target_info))
            case "volcminer":
                return self.get_target_info(VolcminerParser(self.target_info))
            case "goldshell":
                return self.get_target_info(GoldshellParser(self.target_info))
            case "sealminer":
                return self.get_target_info(SealminerParser(self.target_info))
            case "elphapex":
                return self.get_target_info(ElphapexParser(self.target_info))
            case "dragonball":
                return self.get_target_info(DragonballParser(self.target_info))
            case _:
                return self.target_info

    def close_client(self) -> None:
        if self.client:
            logger.debug(" close client.")
            self.client = self.client._close_client()
