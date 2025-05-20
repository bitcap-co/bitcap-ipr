from ...parser import Parser

class GoldshellParser(Parser):
    def parse_subtype(self, obj: dict):
        if "model" in obj:
            self.target["subtype"] = obj["model"]

    def parse_algorithm(self, obj: dict):
        for algo in obj["algos"]:
            if algo["id"] == obj["algo_select"]:
                self.target["algorithm"] = obj["algos"][algo["id"]]["name"]
                break

    def parse_firmware(self, obj: dict):
        if "firmware" in obj:
            self.target["firmware"] = obj["firmware"]

    def parse_system_info(self, obj: dict):
        self.parse_firmware(obj)
        self.parse_subtype(obj)
