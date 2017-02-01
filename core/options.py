class Options(object):
    def __init__(self, scheduler=None, children=None, enabled=False):
        self.scheduler = scheduler if scheduler is not None else {}
        self.enabled = enabled
        self.children = children if children is not None else {}

    def __repr__(self):
        result = {'scheduler': str(self.scheduler),
                  'enabled': str(self.enabled),
                  'children': str(self.children)}
        return str(result)
