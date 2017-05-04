import xml.etree.cElementTree as et
import logging
from jinja2 import Template
import core.config.config

logger = logging.getLogger(__name__)

class Argument(object):
    def __init__(self, key=None, value=None, format='str'):
        """Initializes a new Argument object.
        Args:
            key (str): Name of argument
            value (any): Value of argument
            format (str, optional): Format to which to convert value
        """
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
        """Converts an Argument value to the specified conversion type. The default is type string.
        Args:
            value (): The Argument value to be converted.
            conversion_type (str, optional): The optional type to which to convert.
        Returns:
            The converted value in the specified format.        
        """
        output = value
        if any(conversion_type == string_type for string_type in ['str', 'string', 'unicode']):
            try:
                output = str(output)
            except ValueError:
                logger.warning('Conversion of argument {0} to {1}  failed'.format(value, conversion_type))
                return output
        elif conversion_type == 'int':
            try:
                output = int(output)
            except (ValueError, TypeError):
                logger.warning('Conversion of argument {0} to {1}  failed'.format(value, conversion_type))
                return output
        else:
            logger.error('Unhandled conversion type {0} encountered in argument'.format(conversion_type))
        return output

    def template(self, **kwargs):
        """Renders the template, using JINJA templating, of the Argument object.
        Args:
            kwargs (dict): Keyword arguments to be passed into the render() function.
        Returns:
            The template representation, from the render() function, of the Argument value.
        """
        template = Template(str(self.value))
        self.templated = template.render(core.config.config.JINJA_GLOBALS, **kwargs)
        return self.templated

    def to_xml(self):
        """Converts Argument object to XML
        Returns:
            XML of Argument object, or None if key is None.
        """
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
            except Exception as e:
                logger.error('Unhandled conversion exception found when validating arguments: {0}'.format(e))
                return False
        return arg['name'] == self.key and arg['type'] == self.format

    def validate(self, possible_args):
        """Validates an Argument based on its type.
        Args:
            possible_args(list of dicts): List of dictionary representation of arguments to be validated.
        Returns:
            True or False based on whether or not the arguments were all validated.
        """
        return any(self.__test_validation_match(arg) for arg in possible_args)

    def validate_function_args(self, app, action):
        """Validates arguments for an app action.
        Args:
            app (str): The name of the app for which to validate against.
            action (str): The action for the specified app to validate against.
        Returns:
            True or False based on whether or not the arguments were all validated.
        """
        if app in core.config.config.function_info['apps'] and action in core.config.config.function_info['apps'][app]:
            return self.validate(core.config.config.function_info['apps'][app][action]['args'])
        return False

    def as_json(self):
        """Gets the JSON representation of the Argument object.
        Returns:
            The JSON representation of the Argument object.
        """
        return {"key": str(self.key),
                "value": str(self.value),
                "format": str(self.format)}

    @staticmethod
    def from_json(json):
        """Converts the JSON to an Argument object.
        Args:
            json (JSON dict): The JSON to be converted.
        Returns:
            The Argument object from the JSON representation.
        """
        return Argument(key=json['key'], value=json['value'], format=json['format'])
