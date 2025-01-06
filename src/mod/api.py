import logging
import socket
import json
import requests
from requests.auth import HTTPDigestAuth

logger = logging.getLogger(__name__)


def retrieve_iceriver_mac_addr(ip_addr: str):
    with requests.Session() as s:
        host = f"http://{ip_addr}"
        try:
            s.head(host, timeout=3.0)
        except requests.exceptions.ConnectTimeout:
            logger.error("retrieve_iceriver_mac_addr : failed to make connection to miner. abort!")
            return "ice-river"
        res = s.post(
            url=f"{host}/user/ipconfig",
            data={"post": 1},
            headers={"Referer": host},
        )
        r_json = res.json()["data"]
        if "mac" in r_json:
            return r_json["mac"]


def retrieve_antminer_data(endpoints: list, login_passwd: str, obj: dict) -> dict:
    for endp in range(0, (len(endpoints))):
        logger.debug(f"retrieve_antminer_data : authenticate endp {endp}.")
        try:
            s = requests.Session()
            res = s.get(endpoints[endp], auth=HTTPDigestAuth("root", login_passwd))
            if res.status_code == 401:
                logger.warning("retrieve_antminer_data : authentication login failed. Try default...")
                # first pass failed
                login_passwd = "root"
                res = s.head(
                    endpoints[endp], auth=HTTPDigestAuth("root", login_passwd)
                )
                # second pass fail; abort
                if res.status_code == 401:
                    logger.error("retrieve_antminer_data : authentication fail. abort!")
                    endp = -1
                    break
            if res.status_code == 200:
                logger.debug("retrieve_antminer_data : authentication success.")
                break
        except requests.exceptions.ConnectionError:
            logger.error(f"retrieve_antminer_data : failed to make connection to miner. abort!")
            endp = -1
            break
    logger.debug("retrieve_antminer_data : parse json data.")
    match endp:
        case 0:
            r_json = res.json()
            if "serial" in r_json:
                obj["serial"] = res.json()["serial"]
            if "miner" in r_json:
                obj["subtype"] = res.json()["miner"][9:]
        case 1:
            r_json = res.json()
            if "serinum" in r_json:
                obj["serial"] = res.json()["serinum"]
            if "minertype" in r_json:
                obj["subtype"] = res.json()["minertype"][9:]
        case -1:
            # failed to authenticate
            obj["serial"] = "Failed Auth"
            obj["subtype"] = "Failed Auth"
    s.close()
    return obj


def retrieve_iceriver_data(ip_addr: str, obj: dict) -> dict:
    with requests.Session() as s:
        host = f"http://{ip_addr}"
        try:
            s.head(host, timeout=3.0)
        except requests.exceptions.ConnectTimeout:
            logger.error("retrieve_iceriver_data : failed to make connection to miner. abort!")
            return obj
        res = s.post(
            url=f"{host}/user/userpanel",
            data={"post": 4},
            headers={"Referer": host},
        )
        logger.debug("retreive_iceriver_data : parse json data.")
        r_json = res.json()["data"]
        if "model" in r_json:
            if r_json["model"] == "none":
                if "softver1" in r_json:
                    model = "".join(r_json["softver1"].split("_")[-2:])
                    obj["subtype"] = model[model.rfind("ks"):model.rfind("miner")].upper()
            else:
                obj["subtype"] = r_json["model"]
        return obj


def retrieve_whatsminer_data(ip_addr: str, cmd: dict, obj: dict) -> dict:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(3.0)
        try:
            s.connect((ip_addr, 4028))
        except TimeoutError:
            logger.error("retrieve_whatsminer_data : failed to connect to miner. abort!")
            return obj
        s.send(json.dumps(cmd).encode("utf-8"))
        data = s.recv(4096)
        logger.debug("retreive_whatsminer_data : parse json data.")
        try:
            r_json = json.loads(data.decode())
            if "Model" in r_json["DEVDETAILS"][0]:
                obj["subtype"] = r_json["DEVDETAILS"][0]["Model"]
        except Exception:
            pass
    return obj
