from connexion.apis.abstract import AbstractAPI
import os.path
from core.config.paths import apps_path
from connexion.resolver import Resolver,Resolution
from connexion.lifecycle import ConnexionRequest
from connexion.apis.flask_api import Jsonifier
from connexion.operation import Operation


try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

class WalkoffAppDefinition(AbstractAPI, object):
    def __init__(self, name, instance):
        self.name = name
        self.path = os.path.abspath(os.path.join(apps_path, name, "functions.yaml"))
        self.operations = {}
        self.instance = instance
        self.resolver = WalkoffResolver(self.name, instance)
        self.jsonifier = Jsonifier
        super(WalkoffAppDefinition, self).__init__(self.path, {}, resolver=self.resolver)

    def _set_base_path(self, base_path):
        super(WalkoffAppDefinition, self)._set_base_path(base_path)

    def _add_operation_internal(self, method, path, operation):
        operation_id = operation.operation.get("operationId")
        self.operations[operation_id] = operation

    def add_auth_on_not_found(self, security, security_definitions):
        return

    def add_swagger_json(self):
        return

    def add_swagger_ui(self):
        return

    @classmethod
    def get_request(cls, *args, **params):
        method = params["api"].operations["Main." + params["action"]].method
        type = params["api"].operations["Main." + params["action"]].operation
        url = params["api"].operations["Main." + params["action"]].path
        result = {"headers": {}, "form": {}, "query": {}, "body": {}, "json": {}, "files": {}, "path_params": {},
                  "context": {}}
        if "parameters" in type.keys():
            for parameter in type["parameters"]:
                if parameter["in"] not in result:
                    result[parameter["in"]] = {}
                result[parameter["in"]][parameter["name"]] = params["args"][parameter["name"]]
        result = cls.formatArgs(result)
        request = ConnexionRequest(url, method, **result)
        return request

    #@classmethod
    def get_response(self, response, mimetype=None, request=None):
        #print(cls, response, mimetype, request)
        action = "Main." + request.url[1:]
        content_type = self.operations[action].produces[-1]
        return response


    @classmethod
    def format_response(cls, response):
        return

    @staticmethod
    def formatArgs(args):
        for type in args:
            if type == "query":
                #result[type] = MultiDict(args[type])
                args[type] = args[type]
        return args


class WalkoffResolver(object):
    def __init__(self, name, instance):
        self.name = name
        self.instance = instance

    def resolve(self, operation):
        try:
            opid = operation.operation.get("operationId")
            #fn = get_function_from_name("apps." + self.name + ".main." + operation.operation.get("operationId"))
            fn = getattr(self.instance, opid.split(".")[1])
        except Exception as e:
            print("EXCEPTION: Could not resolve function")
            return None
        return Resolution(fn, opid)


