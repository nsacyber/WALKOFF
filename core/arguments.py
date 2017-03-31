import xml.etree.cElementTree as et

from jinja2 import Template

from core.config import config


class Argument(object):
    def __init__(self, key=None, value=None, format='str'):
        self.key = key
        self.format = format
        self.value = Argument.convert(value=value, conversion_type=self.format)
        self.templated = None

    def __call__(self):
        if self.templated:
            return self.templated
        return self.value

    @staticmethod
    def convert(value=None, conversion_type='str'):
        output = value
        if any(conversion_type == string_type for string_type in ['str', 'string', 'unicode']):
            try:
                output = str(output)
            except ValueError:
                return output
        elif conversion_type == 'int':
            try:
                output = int(output)
            except (ValueError, TypeError):
                return output
        return output

    def template(self, **kwargs):
        template = Template(str(self.value))
        self.templated = template.render(config.JINJA_GLOBALS, **kwargs)
        return self.templated

    def to_xml(self):
        if self.key:
            elem = et.Element(self.key)
            elem.text = str(self.value)
            elem.set("format", self.format)
            return elem
        else:
            return None

    def __repr__(self):
        output = {'key': self.key,
                  'value': str(self.value),
                  'type': self.format}
        return str(output)

    def __test_validation_match(self, arg):
        if arg['type'] != self.format:
            try:
                self.value = Argument.convert(value=self.value, conversion_type=arg['type'])
            except:
                return False
        return arg['name'] == self.key and arg['type'] == self.format

    def __validate(self, possible_args):
        if not possible_args:
            return True
        return any(self.__test_validation_match(arg) for arg in possible_args)

    def validate_filter_args(self, action, num_args):
        if action in config.function_info['filters']:
            possible_args = config.function_info['filters'][action]['args']
            return len(list(possible_args)) == num_args and self.__validate(possible_args)
        return False

    def validate_flag_args(self, action):
        if action in config.function_info['flags']:
            return self.__validate(config.function_info['flags'][action]['args'])
        return False

    def validate_function_args(self, app, action):
        if app in config.function_info['apps'] and action in config.function_info['apps'][app]:
            return self.__validate(config.function_info['apps'][app][action]['args'])
        return False

    def as_json(self):
        return {"key": str(self.key),
                "value": str(self.value),
                "format": str(self.format)}

    @staticmethod
    def from_json(json):
        return Argument(key=json['key'], value=json['value'], format=json['format'])
