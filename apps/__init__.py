from server.appdevice import App as _App


class App(object):
    def __init__(self, app, device):
        self.app = app
        self.device = device

    def get_all_devices(self):
        """ Gets all the devices associated with this app """
        return _App.get_all_devices_for_app(self.app)

    def get_device(self):
        """ Gets the device associated with this app """
        return _App.get_device(self.app, self.device)

    def shutdown(self):
        """ When implemented, this menthod performs shutdown procedures for the app """
        pass