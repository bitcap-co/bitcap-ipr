class Parser:
    def __init__(self, target: dict):
        self.target = target.copy()

    def get_target(self):
        return self.target
