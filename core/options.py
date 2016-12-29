class Options(object):
    def __init__(self, scheduler={}, children={}, enabled=False):
        self.scheduler = scheduler
        self.enabled = enabled
        self.children =  children

    def __repr__(self):
        result = {}
        result["scheduler"] = str(self.scheduler)
        result["enabled"] = str(self.enabled)
        result["children"] = str(self.children)
        return str(result)
