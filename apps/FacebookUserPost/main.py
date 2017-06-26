from apps import App, action
import requests


class Main(App):

    def __init__(self, name=None, device=None):
        self.user_id = self.get_device().username
        self.user_access_token = self.get_device().get_password()
        App.__init__(self, name, device)

    @action
    def post_to_user_wall(self, message):
        msg = message.replace(" ", "+")
        url = ('https://graph.facebook.com/v2.9/' + self.user_id + '/feed?'
               'message=' + msg + '&access_token=' + self.get_device().get_password())
        return (requests.post(url, verify=False)).text
