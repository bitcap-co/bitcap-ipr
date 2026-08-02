
from src.mod.ipr_asic.rpc import CGMinerRPCClient


class IPolloRPCClient(CGMinerRPCClient):
    def __init__(self, ip: str, port: int = 4028, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)
