import logging
from PySide6.QtCore import (
    QObject,
    QTimer,
)

from mod.api import settings
from mod.api.parser import Parser
from mod.api.errors import (
    FailedConnectionError,
    AuthenticationError,
)
from .miners.bitmain import BitmainHTTPClient, BitmainParser
from .miners.iceriver import IceriverHTTPClient, IceriverParser
from .miners.whatsminer import WhatsminerRPCClient, WhatsminerParser
from .miners.volcminer import VolcminerHTTPClient, VolcminerParser
from .miners.goldshell import GoldshellHTTPClient, GoldshellParser
from .miners.sealminer import SealminerHTTPClient, SealminerParser

logger = logging.getLogger(__name__)


class APIClient:
    def __init__(self, parent: QObject):
        self.parent = parent
        self.client = None
        self.locate_duration = None
        self.target_info = {
            "serial": "N/A",
            "subtype": "N/A",
            "algorithm": "N/A",
            "firmware": "N/A",
            "platform": "N/A",
        }

    def get_client(self):
        return self.client

    def create_bitmain_client(self, ip_addr: str, passwd: str):
        try:
            self.client = BitmainHTTPClient(ip_addr, passwd)
        except (
            FailedConnectionError,
            AuthenticationError,
        ) as err:
            logger.error(err)

    def create_iceriver_client(self, ip_addr: str, pb_key: str):
        try:
            self.client = IceriverHTTPClient(ip_addr, pb_key)
        except FailedConnectionError as err:
            logger.error(err)

    def create_whatsminer_client(
        self,
        ip_addr: str,
        passwd: str,
    ):
        try:
            self.client = WhatsminerRPCClient(ip_addr, passwd)
        except FailedConnectionError as err:
            logger.error(err)

    def create_volcminer_client(self, ip_addr: str, passwd: str):
        try:
            self.client = VolcminerHTTPClient(ip_addr, passwd)
        except (FailedConnectionError, AuthenticationError) as err:
            logger.error(err)

    def create_goldshell_client(self, ip_addr: str, passwd: str):
        try:
            self.client = GoldshellHTTPClient(ip_addr, passwd)
        except (FailedConnectionError, AuthenticationError) as err:
            logger.error(err)

    def create_sealminer_client(self, ip_addr: str, passwd: str):
        try:
            self.client = SealminerHTTPClient(ip_addr, passwd)
        except (FailedConnectionError, AuthenticationError) as err:
            logger.error(err)

    def create_client_from_type(self, miner_type: str, ip_addr: str, auth_str: str):
        match miner_type:
            case "antminer":
                self.create_bitmain_client(ip_addr, auth_str)
            case "iceriver":
                self.create_iceriver_client(ip_addr, auth_str)
            case "whatsminer":
                self.create_whatsminer_client(ip_addr, auth_str)
            case "volcminer":
                self.create_volcminer_client(ip_addr, auth_str)
            case "goldshell":
                self.create_goldshell_client(ip_addr, auth_str)
            case "sealminer":
                self.create_sealminer_client(ip_addr, auth_str)

    def locate_miner(self, miner_type: str):
        self.locate_duration = QTimer(self.parent)
        self.locate_duration.setSingleShot(True)
        self.locate_duration.timeout.connect(self.stop_locate)
        duration_ms = settings.get("locate_duration_ms", 10000)
        logger.info(" locate miner for 10000ms.")
        match miner_type:
            case "antminer":
                try:
                    self.client.blink(True)
                    self.locate_duration.start(duration_ms)
                except AuthenticationError as err:
                    logger.error(err)
                    self.close_client()
            case "iceriver" | "volcminer" | "goldshell" | "sealminer":
                self.client.blink(True)
                self.locate_duration.start(duration_ms)
            case "whatsminer":
                try:
                    self.client.blink()
                    self.close_client()
                except AuthenticationError as err:
                    logger.error(err)
                    self.close_client()

    def stop_locate(self):
        self.client.blink(False)
        self.close_client()

    def get_iceriver_mac_addr(self):
        if self.client:
            mac = self.client.get_mac_addr()
            if mac:
                return mac
        return "ice-river"

    def is_volcminer(self):
        if self.client:
            system_info = self.client.get_system_info()
            if "minertype" in system_info:
                miner_type = system_info["minertype"][:10].strip()
                if miner_type == "VolcMiner":
                    logger.debug(" found VolcMiner.")
                    return True
        return False

    def get_target_info(self, parser: Parser) -> dict[str, str]:
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
            parser.parse_serial(sys)
            devs = self.client.get_dev_details()
            parser.parse_subtype(devs)
            ver = self.client.get_version()
            parser.parse_version_info(ver)
        return parser.get_target()

    def get_target_data_from_type(self, miner_type: str):
        match miner_type:
            case "antminer":
                return self.get_target_info(BitmainParser(self.target_info))
            case "iceriver":
                return self.get_target_info(IceriverParser(self.target_info))
            case "whatsminer":
                return self.get_target_info(WhatsminerParser(self.target_info))
            case "volcminer":
                return self.get_target_info(VolcminerParser(self.target_info))
            case "goldshell":
                return self.get_target_info(GoldshellParser(self.target_info))
            case "sealminer":
                return self.get_target_info(SealminerParser(self.target_info))
            case _:
                return self.target_info

    def close_client(self):
        if self.client:
            logger.debug(" close client.")
            self.client = self.client._close_client()
