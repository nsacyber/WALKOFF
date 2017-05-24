#from connexion.apis.abstract import AbstractAPI
import os.path
from core.config.paths import apps_path
from connexion.resolver import Resolver,Resolution
from connexion.lifecycle import ConnexionRequest
from connexion.apis.flask_api import Jsonifier
from connexion.apis import abstract
from core.config import paths
try:
    from urllib import urlencode
except ImportError:
    from urllib.parse import urlencode

import functools
from swagger_spec_validator.validator20 import validate_apis, validate_definitions, deref
def validate_spec(spec_dict, spec_url='', http_handlers=None):
    """Validates a Swagger 2.0 API Specification given a Swagger Spec.
        :param spec_dict: the json dict of the swagger spec.
        :type spec_dict: dict
        :param spec_url: url from which spec_dict was retrieved. Used for
            dereferencing refs. eg: file:///foo/swagger.json
        :type spec_url: string
        :param http_handlers: used to download any remote $refs in spec_dict with
            a custom http client. Defaults to None in which case the default
            http client built into jsonschema's RefResolver is used. This
            is a mapping from uri scheme to a callable that takes a
            uri.
        :returns: the resolver (with cached remote refs) used during validation
        :rtype: :class:`jsonschema.RefResolver`
        :raises: :py:class:`swagger_spec_validator.SwaggerValidationError`
        """
    swagger_resolver = validate_json(
        spec_dict,
        'walkoff_schema.json',
        spec_url=spec_url,
        http_handlers=http_handlers,
    )

    bound_deref = functools.partial(deref, resolver=swagger_resolver)
    spec_dict = bound_deref(spec_dict)
    apis = bound_deref(spec_dict['paths'])
    definitions = bound_deref(spec_dict.get('definitions', {}))
    validate_apis(apis, bound_deref)
    validate_definitions(definitions, bound_deref)
    return swagger_resolver

import json
from swagger_spec_validator import ref_validators
from jsonschema import RefResolver
from jsonschema.validators import Draft4Validator
def validate_json(spec_dict, schema_path, spec_url='', http_handlers=None):
    """Validate a json document against a json schema.
    :param spec_dict: json document in the form of a list or dict.
    :param schema_path: package relative path of the json schema file.
    :param spec_url: base uri to use when creating a
        RefResolver for the passed in spec_dict.
    :param http_handlers: used to download any remote $refs in spec_dict with
        a custom http client. Defaults to None in which case the default
        http client built into jsonschema's RefResolver is used. This
        is a mapping from uri scheme to a callable that takes a
        uri.
    :return: RefResolver for spec_dict with cached remote $refs used during
        validation.
    :rtype: :class:`jsonschema.RefResolver`
    """
    schema_path = os.path.join(paths.schema_path, schema_path)
    with open(schema_path) as schema_file:
        schema = json.loads(schema_file.read())

    schema_resolver = RefResolver('file://{0}'.format(schema_path), schema)

    spec_resolver = RefResolver(spec_url, spec_dict,
                                handlers=http_handlers or {})

    ref_validators.validate(
        spec_dict,
        schema,
        resolver=schema_resolver,
        instance_cls=ref_validators.create_dereffing_validator(spec_resolver),
        cls=Draft4Validator)

    # Since remote $refs were downloaded, pass the resolver back to the caller
    # so that its cached $refs can be re-used.
    return spec_resolver


abstract.validate_spec = validate_spec

class WalkoffAppDefinition(abstract.AbstractAPI, object):
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


