def filter_yaml_extensions(yaml):
    return {key: value for key, value in yaml.items() if not key.startswith('x-')}


class YamlChild(object):
    def __init__(self, field, child_class, expansion=None):
        self.field = field
        self.child_class = child_class
        self.expansion = expansion

    def construct_child(self, yaml):
        if self.field in yaml:
            if self.expansion:
                self._expand(yaml)
            yaml[self.field] = self.child_class.from_api_yaml(yaml[self.field])

    def _expand(self, yaml):
        expanded = []
        for field_name, field_yaml in yaml[self.field].items():
            field_yaml[self.expansion] = field_name
            expanded.append(field_yaml)
        yaml[self.field] = expanded


class YamlConstructable(object):

    @classmethod
    def from_api_yaml(cls, yaml, **additional_keys):
        if isinstance(yaml, list):
            return cls._from_api_yaml_list(yaml, **additional_keys)
        else:
            return cls._from_api_yaml_dict(yaml, **additional_keys)

    @classmethod
    def _from_api_yaml_list(cls, yaml, **additional_keys):
        return [cls.from_api_yaml(element, **additional_keys) for element in yaml]

    @classmethod
    def _from_api_yaml_dict(cls, yaml, **additional_keys):
        filtered_yaml = filter_yaml_extensions(yaml)
        if hasattr(cls, '_children'):
            for child in cls._children:
                child.construct_child(filtered_yaml)
        if hasattr(cls, 'schema'):
            filtered_yaml = cls._extract_schema(filtered_yaml)
        filtered_yaml.update(additional_keys)
        return cls(**filtered_yaml)

    @classmethod
    def _extract_schema(cls, filtered_yaml):
        class_attrs = {field for field in vars(cls) if not field.startswith('__') and field != 'schema'}
        new_yaml = {}
        schema = {}
        for key, value in filtered_yaml.items():
            if key in class_attrs:
                new_yaml[key] = value
            else:
                schema[key] = value
        new_yaml['schema'] = schema
        return new_yaml
