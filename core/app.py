from abc import ABCMeta, abstractmethod


class App(object):
    __metaclass__ = ABCMeta

    def __init__(self, app=None, device=None):
        self.app = app
        self.getConfig(device)

    def getConfig(self, device):
        from server import device as d

        if device:
            query = d.Device.query.filter_by(app=self.app, name=device).first()
            if query:
                self.config = query

        else:
            self.config = {}

    @abstractmethod
    def shutdown(self):
        return
