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
                    slug: str = obj["softver1"]
                    model_name = slug.split("_")[-2]
                    if model_name == "10306":
                        self.target["subtype"] = "AL3"
                    else:
                        self.target["subtype"] = model_name.upper()
            else:
                self.target["subtype"] = obj["model"]

    def parse_algorithm(self, obj: Dict[str, Any]) -> None:
        if "algo" in obj:
            if not obj["algo"] == "none":
                self.target["algorithm"] = obj["algo"]
            else:
                if self.target["subtype"] == "AL3":
                    self.target["algorithm"] = "blake3"
                elif self.target["subtype"].__contains__("KS"):
                    self.target["algorithm"] = "kHeavyHash"

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
