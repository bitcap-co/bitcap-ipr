import logging
from PyQt6.QtCore import QObject
from .errors import (
    FailedConnectionError,
    AuthenticationError
)
from .bitmain import BitmainClient, BitmainParser

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
            self.client = None

    def create_iceriver_client(self, ip_addr: str, auth_str: str = None):
        pass

    def create_whatsminer_client(self, ip_addr: str, port: int = 4028, auth_str: str = "admin"):
        pass

    def create_client_from_type(self, miner_type: str, ip_addr: str, auth_str: str):
        pass

    def get_iceriver_mac_addr(self):
        pass

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
        pass

    def get_whatsminer_target_data(self):
        pass

    def get_target_data_from_type(self, miner_type: str):
        pass


