import logging
from PyQt6.QtCore import QObject
from .errors import (
    FailedConnectionError,
    AuthenticationError,
    MissingAPIKeyError
)
from .bitmain import BitmainClient, BitmainParser
from .iceriver import IceriverClient, IceriverParser
from .whatsminer import WhatsminerClient, WhatsminerParser

logger = logging.getLogger(__name__)

# self.api_client = APIClient(self)
class APIClient():
    def __init__(self, parent: QObject):
        self.parent = parent
        self.client = None
        self.target_info = {
            "serial": "N/A",
            "subtype": "N/A",
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
        ) as exc:
            logger.error(exc)

    def create_iceriver_client(self, ip_addr: str, auth_str: str = None):
        try:
            self.client = IceriverClient(ip_addr, auth_str)
        except FailedConnectionError as exc:
            logger.error(exc)

    def create_whatsminer_client(self, ip_addr: str, port: int = 4028, auth_str: str = None):
        try:
            self.client = WhatsminerClient(ip_addr, port, admin_passwd=auth_str)
        except FailedConnectionError as err:
            logger.error(err)

    def create_client_from_type(self, miner_type: str, ip_addr: str, auth_str: str):
        pass

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
        parser.parse_subtype(system_info)
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
        return parser.get_target()

    def get_target_data_from_type(self, miner_type: str):
        pass


