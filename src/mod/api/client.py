import logging
from PyQt6.QtCore import QObject, QTimer, pyqtSignal
from .errors import (
    FailedConnectionError,
    AuthenticationError,
    MissingAPIKeyError
)
from .bitmain import BitmainClient, BitmainParser
from .iceriver import IceriverClient, IceriverParser
from .whatsminer import WhatsminerClient, WhatsminerParser

logger = logging.getLogger(__name__)


class APISignals(QObject):
    locate_complete = pyqtSignal()


class APIClient():
    def __init__(self, parent: QObject):
        self.parent = parent
        self.signals = APISignals()
        self.client = None
        self.target_info = {
            "serial": "N/A",
            "subtype": "N/A",
            "algorithm": "N/A",
            "firmware": "N/A",
            "platform": "N/A"
        }

    def get_client(self):
        if self.client:
            return self.client

    def create_bitmain_client(self, ip_addr: str, auth_str: str):
        if not auth_str:
            auth_str = "root"
        try:
            self.client = BitmainClient(ip_addr, auth_str)
        except (
            FailedConnectionError,
            AuthenticationError
        ) as err:
            logger.error(err)

    def create_iceriver_client(self, ip_addr: str, auth_str: str):
        try:
            self.client = IceriverClient(ip_addr, auth_str)
        except FailedConnectionError as err:
            logger.error(err)

    def create_whatsminer_client(self, ip_addr: str, port: int = 4028, auth_str: str = None):
        try:
            self.client = WhatsminerClient(ip_addr, port, admin_passwd=auth_str)
        except FailedConnectionError as err:
            logger.error(err)

    def create_client_from_type(self, miner_type: str, ip_addr: str, auth_str: str):
        match miner_type:
            case "antminer":
                self.create_bitmain_client(ip_addr, auth_str)
            case "iceriver":
                self.create_iceriver_client(ip_addr, auth_str)
            case "whatsminer":
                self.create_whatsminer_client(ip_addr, auth_str=auth_str)

    def locate_miner(self, miner_type: str):
        locate_duration = QTimer(self.parent)
        locate_duration.setSingleShot(True)
        locate_duration.timeout.connect(self.stop_locate)
        logger.info(" locate miner for 10000ms.")
        match miner_type:
            case "antminer":
                if self.client.is_custom:
                    try:
                        self.client.unlock_vnish_session()
                    except AuthenticationError as err:
                        logger.error(err)
                self.client.blink(True)
                locate_duration.start(10000)
            case "iceriver":
                self.client.blink(True)
                locate_duration.start(10000)
            case "whatsminer":
                try:
                    self.client.blink()
                    self.signals.locate_complete.emit()
                except AuthenticationError as err:
                    logger.error(err)

    def stop_locate(self):
        self.client.blink(False)
        self.signals.locate_complete.emit()

    def get_iceriver_mac_addr(self):
        if self.client:
            try:
                mac = self.client.get_mac_address()
            except MissingAPIKeyError as err:
                logger.error(err)
                return "ice-river"
            return mac
        return "ice-river"

    def get_antminer_target_data(self):
        parser = BitmainParser(self.target_info)
        result = parser.get_target()
        if not self.client:
            for k in result.keys():
                result[k] = "Failed"
            return result
        system_info = self.client.run_command("GET", "get_system_info")
        parser.parse_firmware(system_info)
        if not self.client.is_custom:
            parser.parse_algorithm(system_info)
            log = self.client.get_system_log()
            parser.parse_platform(log)
        else:
            parser.parse_platform(system_info)
        parser.parse_common(system_info)
        return parser.get_target()

    def get_iceriver_target_data(self):
        parser = IceriverParser(self.target_info)
        result = parser.get_target()
        if not self.client:
            for k in result.keys():
                result[k] = "Failed"
            return result
        try:
            system_info = self.client.get_system_info()
        except MissingAPIKeyError as err:
            logger.error(err)
            for k in result.keys():
                result[k] = "Missing Auth"
            return result
        parser.parse_all(system_info)
        return parser.get_target()

    def get_whatsminer_target_data(self):
        parser = WhatsminerParser(self.target_info)
        result = parser.get_target()
        if not self.client:
            for k in result.keys():
                result[k] = "Failed"
            return result
        devs = self.client.get_dev_details()
        parser.parse_subtype(devs)
        version_info = self.client.get_version()
        parser.parse_firmware(version_info)
        parser.parse_platform(version_info)
        return parser.get_target()

    def get_target_data_from_type(self, miner_type: str):
        match miner_type:
            case "antminer":
                return self.get_antminer_target_data()
            case "iceriver":
                return self.get_iceriver_target_data()
            case "whatsminer":
                return self.get_whatsminer_target_data()

    def close_client(self):
        if self.client:
            logger.debug(" close client.")
            self.client = self.client.close_client()
