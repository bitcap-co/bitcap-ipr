from string import Template
from typing import Any

from pydantic import BaseModel, Field

from mod.apiv2 import settings
from mod.apiv2.base import BaseHTTPClient
from mod.apiv2.rpc.cgminer import Pool, Status, Version


class NetworkInfo(BaseModel):
    command: str
    protocol: str
    ip: str
    mask: str
    gateway: str
    dns: str
    hostname: str


class IPReport(BaseModel):
    command: str
    serial: str = Field(alias="SerialNo")
    ip: str
    mac: str
    model: str
    version: str
    hostname: str
    pubkey: str = Field(alias="pubKey")
    tpm_pubkey: str = Field(alias="tpmPubKey")
    cb_serial: str = Field(alias="CBSerialNo")
    chassis_serial: str = Field(alias="ChassisSerialNo")
    hb_serials: list[str] = Field(default_factory=list[str], alias="HBSerialNo")
    internal_type: str = Field(alias="InternalType")


class Mode(BaseModel):
    pass


class LED(BaseModel):
    code: int
    led1: int = Field(alias="LED1")
    led2: int = Field(alias="LED2")
    msg: str = Field(alias="Msg")


class Token(BaseModel):
    name: str = Field(alias="Name")
    when: int = Field(alias="When")
    token: str = Field(alias="Token")


class Response(BaseModel):
    id: int
    status: list[Status] = Field(alias="STATUS")
    version: list[Version] | None = Field(None, alias="VERSION")
    summary: list[dict[str, Any]] | None = Field(None, alias="SUMMARY")
    stats: list[dict[str, Any]] | None = Field(None, alias="STATS")
    devs: list[dict[str, Any]] | None = Field(None, alias="DEVS")
    dev_details: list[dict[str, Any]] | None = Field(None, alias="DEVDETAILS")
    pools: list[Pool] | None = Field(None, alias="POOLS")
    network: list[NetworkInfo] | None = Field(None, alias="Network")
    ip_report: list[IPReport] | None = Field(None, alias="IPReport")
    led: list[LED] | None = Field(None, alias="LED")
    mode: list[Mode] | None = Field(None, alias="Mode")
    token: list[Token] | None = Field(None, alias="Token")

    def error(self) -> str | None:
        for status in self.status:
            match status.status:
                case "E" | "F":
                    return f"received API error ({status.code}) {status.msg} - {status.description}"
                case _:
                    return None


class AuradineHTTPClient(BaseHTTPClient):
    def __init__(self, ip: str, port: int = 8080, alt_pwd: str | None = None) -> None:
        super().__init__(ip, port, alt_pwd)
        self.command_path = Template("${command}")

        self.username: str = "admin"
        if alt_pwd:
            settings.set_auth_alt("auradine", alt_pwd)
        self.passwds = settings.get_auth_list("auradine")

    def authenticate(self) -> None:
        return super().authenticate()

    def get_hostname(self) -> str:
        return super().get_hostname()

    def get_mac_addr(self) -> str:
        return super().get_mac_addr()

    def get_api_version(self) -> str:
        return super().get_api_version()

    def get_system_info(self) -> dict:
        return super().get_system_info()

    def get_network_info(self) -> dict:
        return super().get_network_info()

    def log(self, *args, **kwargs) -> dict:
        return super().log(*args, **kwargs)

    def summary(self) -> dict:
        return super().summary()

    def get_miner_conf(self) -> dict:
        return super().get_miner_conf()

    def set_miner_conf(self, *args, **kwargs) -> dict:
        return super().set_miner_conf(*args, **kwargs)

    def pools(self) -> list[dict]:
        return super().pools()

    def get_pool_conf(self) -> list[dict]:
        return super().get_pool_conf()

    def get_miner_status(self) -> dict:
        return super().get_miner_status()

    def get_blink_status(self) -> dict:
        return super().get_blink_status()

    def blink(self, enabled: bool, *args, **kwargs) -> dict:
        return super().blink(enabled, *args, **kwargs)

    def update_pool_conf(
        self, urls: list[str], users: list[str], passwds: list[str]
    ) -> dict:
        return super().update_pool_conf(urls, users, passwds)
