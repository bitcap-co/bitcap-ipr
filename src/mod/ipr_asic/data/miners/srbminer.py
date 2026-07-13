# Copyright (C) 2024-2026 Matthew Wertman <matt@bitcap.co>
#
# This file is part of bitcap-ipr
# Licensed under the GNU General Public License v3.0; see LICENSE

from typing import Any

from mod.ipr_asic.data import BaseParser, MinerAlgorithm, MinerType

# marketing/vendor tokens stripped when building a readable GPU model name.
_GPU_MODEL_NOISE = {"nvidia", "amd", "intel", "geforce", "radeon"}


def _format_gpu_model(model: str) -> str:
    """Turn an SRBMiner device model into a readable name.

    e.g. "nvidia_geforce_rtx_3070" -> "RTX 3070".
    """
    parts = [p for p in model.split("_") if p and p.lower() not in _GPU_MODEL_NOISE]
    if not parts:
        parts = [p for p in model.split("_") if p]
    cleaned: list[str] = []
    for p in parts:
        # short alpha tokens are acronyms (rtx, gtx, rx); keep numbers as-is.
        if p.isalpha() and len(p) <= 3:
            cleaned.append(p.upper())
        elif p.isalpha():
            cleaned.append(p.capitalize())
        else:
            cleaned.append(p)
    return " ".join(cleaned)


class SRBMinerParser(BaseParser):
    def __init__(self) -> None:
        super().__init__()
        self.data.type = MinerType.HIVEGPU
        self.data.platform = "HiveOS"

    def parse_api_version(self, obj: dict[str, Any]) -> None:
        self.data.api_version = obj["miner_version"]

    def parse_uptime(self, obj: dict[str, Any]) -> None:
        self.data.uptime = obj["mining_time"]

    def parse_hostname(self, obj: dict[str, Any]) -> None:
        self.data.hostname = obj["rig_name"]

    def parse_mac(self, obj: Any) -> None:
        # not exposed by the SRBMiner API; filled from the IP Report.
        return super().parse_mac(obj)

    def parse_serial(self, obj: Any) -> None:
        return super().parse_serial(obj)

    def parse_type(self, obj: Any) -> None:
        return super().parse_type(obj)

    def parse_subtype(self, obj: dict[str, Any]) -> None:
        # report as "Nx GPU_MODEL" (e.g. "4x RTX 3070").
        gpus = obj["gpu_devices"]
        if not gpus:
            return
        count = obj["total_gpu_workers"] or len(gpus)
        model = _format_gpu_model(gpus[0]["model"])
        self.data.subtype = f"{count}x {model}" if model else f"{count}x GPU"

    def parse_algorithm(self, obj: dict[str, Any]) -> None:
        algos = obj["algorithms"]
        if algos:
            self.data.algorithm = MinerAlgorithm.from_value(algos[0]["name"])

    def parse_firmware(self, obj: dict[str, Any]) -> None:
        return super().parse_firmware(obj)

    def parse_platform(self, obj: Any) -> None:
        return super().parse_platform(obj)

    def parse_system_info(self, obj: Any) -> None:
        return super().parse_system_info(obj)

    def parse_summary(self, obj: Any) -> None:
        self.parse_uptime(obj)

    def parse_pools(self, obj: list[dict[str, Any]]) -> None:
        for pool in obj:
            if not pool.get("url"):
                continue
            self.data.stratum_url = pool["url"]
            if "." in pool["user"]:
                user, worker = pool["user"].split(".", 1)
                self.data.username = user
                self.data.worker_name = worker
            else:
                self.data.username = pool["user"]
            break
