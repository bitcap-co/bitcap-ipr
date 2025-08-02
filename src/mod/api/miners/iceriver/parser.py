from typing import Dict, Any

from ...parser import Parser


class IceriverParser(Parser):
    def __init__(self, target: Dict[str, str]):
        super().__init__(target)

    def parse_serial(self, obj: Dict[str, Any]) -> None:
        return super().parse_serial(obj)

    def parse_subtype(self, obj: Dict[str, Any]) -> None:
        if "model" in obj:
            if obj["model"] == "none":
                if "softver1" in obj:
                    model = "".join(obj["softver1"].split("_")[-2:])
                    self.target["subtype"] = model[
                        model.rfind("ks") : model.rfind("miner")
                    ].upper()
            else:
                self.target["subtype"] = obj["model"]

    def parse_algorithm(self, obj: Dict[str, Any]) -> None:
        if "algo" in obj:
            if not obj["algo"] == "none":
                self.target["algorithm"] = obj["algo"]

    def parse_firmware(self, obj: Dict[str, Any]) -> None:
        if "softver1" in obj:
            self.target["firmware"] = obj["softver1"]

    def parse_platform(self, obj: Dict[str, Any]) -> None:
        return super().parse_platform(obj)

    def parse_system_info(self, obj: Dict[str, Any]) -> None:
        return super().parse_system_info(obj)

    def parse_pools(self, obj: Dict[str, Any]) -> None:
        for pool in obj:
            if pool["connect"]:
                self.target["pool"] = pool["addr"]
                self.target["worker"] = pool["user"]
                break
