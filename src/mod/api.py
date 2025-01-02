import logging
import socket
import json
import requests
from requests.auth import HTTPDigestAuth

logger = logging.getLogger(__name__)


def retrieve_iceriver_mac_addr(ip_addr: str):
    with requests.Session() as s:
        host = f"http://{ip_addr}"
        s.head(host)
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
        logger.info(f"retrieve_antminer_data : authenticate endp {endp}.")
        r = requests.get(
            endpoints[endp], auth=HTTPDigestAuth("root", login_passwd)
        )
        # second pass fail; abort
        if r.status_code == 401:
            # first pass failed
            login_passwd = "root"
            r = requests.head(
                endpoints[endp], auth=HTTPDigestAuth("root", login_passwd)
            )
            # second pass fail; abort
            if r.status_code == 401:
                logger.warning("retrieve_antminer_data : authentication fail. abort!")
                endp = -1
                break
        if r.status_code == 200:
            logger.info("retrieve_antminer_data : authentication success.")
            break
    logger.info("retrieve_antminer_data : parse json data.")
    match endp:
        case 0:
            res = requests.get(endpoints[endp])
            r_json = res.json()
            if "serial" in r_json:
                obj["serial"] = r.json()["serial"]
            if "miner" in r_json:
                obj["subtype"] = r.json()["miner"][9:]
        case 1:
            res = requests.get(
                endpoints[endp], auth=HTTPDigestAuth("root", login_passwd)
            )
            r_json = res.json()
            if "serinum" in r_json:
                obj["serial"] = res.json()["serinum"]
            if "minertype" in r_json:
                obj["subtype"] = res.json()["minertype"][9:]
        case -1:
            # failed to authenticate
            obj["serial"] = "Failed auth"
            obj["subtype"] = "Failed auth"
    return obj


def retrieve_iceriver_data(ip_addr: str, obj: dict) -> dict:
    with requests.Session() as s:
        host = f"http://{ip_addr}"
        s.head(host)
        res = s.post(
            url=f"{host}/user/userpanel",
            data={"post": 4},
            headers={"Referer": host},
        )
        logger.info("retreive_iceriver_data : parse json data.")
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
        s.connect((ip_addr, 4028))
        s.send(json.dumps(cmd).encode("utf-8"))
        data = s.recv(4096)
        logger.info("retreive_whatsminer_data : parse json data.")
        try:
            r_json = json.loads(data.decode())
            if "Model" in r_json["DEVDETAILS"][0]:
                obj["subtype"] = r_json["DEVDETAILS"][0]["Model"]
        except Exception:
            pass
    return obj
