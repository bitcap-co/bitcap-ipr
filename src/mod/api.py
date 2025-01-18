import logging
import socket
import json
import requests
from requests.auth import HTTPDigestAuth

logger = logging.getLogger(__name__)

data_obj = {
    "serial": "N/A",
    "subtype": "N/A"
}
bitmain_endpoints = {
    "custom": "api/v1/info",
    "stock": "cgi-bin/get_system_info.cgi"
}


def get_data_obj():
    return data_obj.copy()


def is_custom_bitmain(ip_addr: str) -> bool:
    r = requests.head(f"http://{ip_addr}/{bitmain_endpoints['custom']}")
    if r.status_code == 200:
        return True
    return False


def get_session(host: str, digest=False, login="root"):
    s = requests.Session()
    if digest:
        auth = HTTPDigestAuth("root", login)
        s.auth = auth
    try:
        res = s.head(host, timeout=3.0)
        return (s, res)
    except (
        requests.exceptions.ConnectTimeout,
        requests.exceptions.ConnectionError
    ) as err:
        logger.error(" failed to connect or timeout. abort!")
        return (err, None)


def retrieve_iceriver_mac_addr(ip_addr: str) -> str:
    host = f"http://{ip_addr}"
    s, _ = get_session(host)
    if isinstance(s, requests.sessions.Session):
        res = s.post(
            url=f"{host}/user/ipconfig",
            data={"post": 1},
            headers={"Referer": host},
        )
        s.close()
        r_json = res.json()["data"]
        if "mac" in r_json:
            return r_json["mac"]
    return "ice-river"


def retrieve_antminer_data(ip_addr: str, login_passwd: str) -> dict:
    result = get_data_obj()
    is_custom = is_custom_bitmain(ip_addr)
    if not is_custom:
        host = f"http://{ip_addr}/{bitmain_endpoints['stock']}"
        s, res = get_session(host, True, login_passwd)
        if not isinstance(s, requests.sessions.Session):
            return result
        if res.status_code == 401:
            logger.warning(" authentication login failed. Try default...")
            s, res = get_session(host, True)
            if res.status_code == 401:
                logger.error(" authentication fail. abort!")
                result["serial"] = "Failed Auth"
                result["subtype"] = "Failed Auth"
                return result
        logger.debug(" authentication success.")
    else:
        host = f"http://{ip_addr}/{bitmain_endpoints['custom']}"
        s, _ = get_session(host)
        if not isinstance(s, requests.sessions.Session):
            return result
    res = s.get(host, auth=s.auth, timeout=3.0)
    r_json = res.json()
    logger.debug("retrieve_antminer_data : parse json data.")
    for key in r_json.keys():
        if key in ["serial", "serinum"]:
            result["serial"] = r_json[key]
        if key in ["miner", "minertype"]:
            result["subtype"] = r_json[key][9:]
    s.close()
    return result


def retrieve_iceriver_data(ip_addr: str) -> dict:
    result = get_data_obj()
    host = f"http://{ip_addr}"
    s, _ = get_session(host)
    if not isinstance(s, requests.sessions.Session):
        return result
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
                result["subtype"] = model[model.rfind("ks"):model.rfind("miner")].upper()
        else:
            result["subtype"] = r_json["model"]
    s.close()
    return result


def retrieve_whatsminer_data(ip_addr: str) -> dict:
    result = get_data_obj()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(3.0)
        try:
            s.connect((ip_addr, 4028))
        except TimeoutError:
            logger.error("retrieve_whatsminer_data : failed to connect to miner. abort!")
            return result
        s.send(json.dumps({"cmd": "devdetails"}).encode("utf-8"))
        data = s.recv(4096)
        logger.debug("retreive_whatsminer_data : parse json data.")
        try:
            r_json = json.loads(data.decode())
            if "Model" in r_json["DEVDETAILS"][0]:
                result["subtype"] = r_json["DEVDETAILS"][0]["Model"]
        except Exception:
            pass
    return result
