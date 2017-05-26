from apps import App
import requests


class Main(App):

    def __init__(self, name=None, device=None):
        self.user_id = "No user id provided"
        self.user_access_token = "No user access provided"
        App.__init__(self, name, device)

    def add_facebook_user(self, args={}):
        if all(key in ["user_id", "user_access_token"] for key in args.keys()):
            self.user_id = args["user_id"]()
            self.user_access_token = args["user_access_token"]()
            return 0

    def post_to_user_wall(self, args={}):
        if args["message"]():
            msg = args["message"]().replace(" ", "+")
            url = ('https://graph.facebook.com/v2.9/' + self.user_id + '/feed?'
                   'message=' + msg + '&access_token=' + self.user_access_token)
            return (requests.post(url, verify=False)).text
