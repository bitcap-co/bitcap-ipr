from ...parser import Parser


class IceriverParser(Parser):
    def parse_subtype(self, obj: dict):
        if "model" in obj:
            if obj["model"] == "none":
                if "softver1" in obj:
                    model = "".join(obj["softver1"].split("_")[-2:])
                    self.target["subtype"] = model[
                        model.rfind("ks") : model.rfind("miner")
                    ].upper()
            else:
                self.target["subtype"] = obj["model"]

    def parse_algorithm(self, obj: dict):
        if "algo" in obj:
            if not obj["algo"] == "none":
                self.target["algorithm"] = obj["algo"]

    def parse_firmware(self, obj: dict):
        if "softver1" in obj:
            self.target["firmware"] = obj["softver1"]

    def parse_all(self, obj: dict):
        self.parse_subtype(obj)
        self.parse_algorithm(obj)
        self.parse_firmware(obj)
        return self.target
