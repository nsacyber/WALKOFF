from abc import ABCMeta, abstractmethod
import json

class App(object):
    __metaclass__=ABCMeta

    def __init__(self, app=None, device=None):
        self.app = app
        self.getConfig(device)

    def getConfig(self, device):
        from api.mainAPI import Device
        if device != None and device != "":
            query = Device.query.filter_by(app=self.app, name=device).first()
            if query != None and query != []:
                self.config = query
        else:
            self.config = {}

    @abstractmethod
    def shutdown(self):
        return

