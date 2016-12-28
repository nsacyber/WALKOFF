class Options():
    def __init__(self, scheduler={}, enabled=False):
        self.scheduler = scheduler
        self.enabled = enabled

    def __repr__(self):
        result = {}
        result["scheduler"] = str(self.scheduler)
        result["enabled"] = str(self.enabled)
        return str(result)
