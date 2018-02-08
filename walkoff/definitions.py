def wrap(cls, value):
    return cls(value) if value is not None else None

class ApiData:

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def set_primitives(self, yaml, keys):
        for key in keys:
            if key in yaml:
                setattr(self, key, yaml[key])

    def set_wrappers(self, yaml, mapping):
        for key, value in mapping.items():
            if key in yaml:
                setattr(self, key, value(yaml[key]))

    def set_wrappers_array(self, yaml, mapping):
        for key, value in mapping.items():
            if key in yaml:
                setattr(self, key, [value(x) for x in yaml[key]])
            else:
                setattr(self, key, [])

    def set_wrappers_dict(self, yaml, mapping):
        for key, value in mapping.items():
            if key in yaml:
                setattr(self, key, {key2: wrap(value, value2) for key2, value2 in yaml[key].items()})
            else:
                setattr(self, key, {})

    def set_defaults(self, mapping):
        for key, value in mapping.items():
            if not hasattr(self, key):
                setattr(self, key, value)

class AppApi(ApiData):

    def __init__(self, yaml):
        self.set_wrappers(yaml, {'info': ApiInfo})
        self.set_wrappers_array(yaml, {'tags': ApiTag, 'external_docs': ExternalDoc})
        self.set_wrappers_dict(yaml, {'actions': ActionApi, 'conditions': ConditionApi, 'transforms': TransformApi,
                               'devices': DeviceApi})

class ApiInfo(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['title', 'version', 'description', 'terms_of_service'])
        self.set_wrappers(yaml, {'contact': ApiContact, 'license': ApiLicense})

class ApiContact(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['name', 'url', 'email'])

class ApiLicense(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['name', 'url'])

class ActionApi(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['name', 'run', 'default_return', 'deprecated', 'tags', 'summary', 'description'])
        self.set_wrappers_array(yaml, {'parameters': ParameterApi, 'external_docs': ExternalDoc})
        self.set_wrappers_dict(yaml, {'returns': ReturnApi})

        self.set_defaults({'default_return': 'Success', 'deprecated': False, 'tags': []})

class ConditionApi(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['name', 'run', 'data_in', 'deprecated', 'tags', 'summary', 'description'])
        self.set_wrappers_array(yaml, {'parameters': ParameterApi, 'external_docs': ExternalDoc})
        self.set_wrappers_dict(yaml, {'returns': ReturnApi})

        self.set_defaults({'deprecated': False, 'tags': []})

class TransformApi(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['name', 'run', 'data_in', 'deprecated', 'tags', 'summary', 'description'])
        self.set_wrappers_array(yaml, {'parameters': ParameterApi, 'external_docs': ExternalDoc})
        self.set_wrappers_dict(yaml, {'returns': ReturnApi})

        self.set_defaults({'deprecated': False, 'tags': []})

class DeviceApi(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['name', 'description'])
        self.set_wrappers_array(yaml, {'fields': DeviceFieldApi})

class DeviceFieldApi(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['name', 'description', 'encrypted', 'placeholder', 'required'])
        self.set_primitives(yaml, ['type', 'default', 'minLength'])  # not in spec
        self.set_wrappers(yaml, {'schema': ParameterSchema})

        self.set_defaults({'encrypted': False, 'required': False})

class ParameterApi(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['name', 'example', 'description', 'placeholder', 'required'])
        self.set_primitives(yaml, ['type', 'default', 'minimum'])  # not in spec
        self.set_wrappers(yaml, {'schema': ParameterSchema})

        self.set_defaults({'required': False})

class ReturnApi(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['status', 'description', 'failure', 'examples'])
        self.set_wrappers(yaml, {'schema': ParameterSchema})

        self.set_defaults({'failure': False})

class ExternalDoc(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['description', 'url'])

class ApiTag(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['name', 'description'])
        self.set_wrappers_array(yaml, {'external_docs': ExternalDoc})

class ParameterSchema(ApiData):

    def __init__(self, yaml):
        self.set_primitives(yaml, ['type', 'format', 'multipleOf', 'maximum', 'exclusiveMaximum', 'minimum',
                            'exclusiveMinimum', 'maxLength', 'minLength', 'pattern', 'maxItems', 'minItems',
                            'uniqueItems', 'enum'])
        self.set_primitives(yaml, ['required', 'properties', 'items'])  # not in spec
