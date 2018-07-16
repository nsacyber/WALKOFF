from sqlalchemy import Column, Integer, ForeignKey, String, Text, Boolean, Table
from sqlalchemy_utils import JSONType
from sqlalchemy.orm import relationship
from walkoff.executiondb import Execution_Base
from walkoff.appgateway.validator import *
from .api_info import AppApiInfo, YamlConstructable, YamlChild
from walkoff.appgateway import get_all_actions_for_app
from walkoff.appgateway import get_all_transforms_for_app
from walkoff.appgateway import get_all_conditions_for_app

action_api_tags_table = Table(
    'action_api_tag_association',
    Column('action_api_id', Integer, ForeignKey(Integer, 'action_api.id')),
    Column('api_tag_id', Integer, ForeignKey(Integer, 'api_tag'))
)


class ExternalDoc(YamlConstructable, Execution_Base):
    __tablename__ = 'external_doc'
    id = Column(Integer, primary_key=True)
    action_api_id = Column(Integer, ForeignKey('action_api.id'))
    condition_api_id = Column(Integer, ForeignKey('condition_api.id'))
    transform_api_id = Column(Integer, ForeignKey('transform_api.id'))
    app_api_tag_id = Column(Integer, ForeignKey('app_api_tag.id'))
    url = Column(String(80), nullable=False)
    description = Column(Text)


class ApiTag(Execution_Base):
    __tablename__ = 'api_tag'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)


class ParameterApi(YamlConstructable, Execution_Base):
    __tablename__ = 'parameter_api'
    id = Column(Integer, primary_key=True)
    action_api_id = Column(Integer, ForeignKey('action_api.id'))
    name = Column(String(80), nullable=False)
    schema = Column(JSONType, nullable=False)
    placeholder = Column(String(80))
    required = Column(Boolean, default=False)
    description = Column(Text)
    example = Column(Text)

    def validate(self, value, message_prefix):
        schema = deepcopy(self.schema)
        converted_value = None
        if value is not None:
            if 'type' in schema:  # handle primitive parameter
                converted_value = ParameterApi.validate_primitive(schema, value, message_prefix)
            else:
                converted_value = ParameterApi.validate_json_parameter(schema, value, message_prefix)
        elif self.required:
            message = "In {}: Missing {} parameter '{}'".format(
                message_prefix,
                'primitive' if 'type' in schema else 'object',
                self.name
            )
            logger.error(message)
            raise InvalidArgument(message)

        return converted_value

    @staticmethod
    def validate_json_parameter(schema, value, message_prefix):
        try:
            converted_value = convert_json(schema, value, message_prefix)
            Draft4Validator(
                schema['schema'], format_checker=draft4_format_checker).validate(converted_value)
        except ValidationError as exception:
            message = '{} has invalid input. Input {} does not conform to validators: {}'.format(
                message_prefix,
                value,
                format_exception_message(exception)
            )
            logger.error(message)
            raise InvalidArgument(message)
        return converted_value

    @staticmethod
    def validate_primitive(schema, value, message_prefix):
        primitive_type = schema['type']
        if primitive_type in TYPE_MAP:
            converted_value = validate_primitive_parameter(value, schema, primitive_type, message_prefix)
        elif primitive_type == 'array':
            converted_value = ParameterApi.validate_array_parameter(message_prefix, schema, value)
        else:
            raise InvalidArgument('In {}: Unknown parameter type {}'.format(message_prefix, primitive_type))
        return converted_value

    @staticmethod
    def validate_array_parameter(message_prefix, schema, value):
        try:
            converted_value = convert_array(schema, value, message_prefix)
            if 'items' in schema and schema['items']['type'] in ('user', 'role'):
                handle_user_roles_validation(schema['items'])

            Draft4Validator(
                schema, format_checker=draft4_format_checker).validate(converted_value)
        except ValidationError as exception:
            message = '{} has invalid input. Input {} does not conform to validators: {}'.format(
                message_prefix,
                value,
                format_exception_message(exception)
            )
            logger.error(message)
            raise InvalidArgument(message)
        return converted_value


class ReturnApi(YamlConstructable, Execution_Base):
    __tablename__ = 'return_api'
    id = Column(Integer, primary_key=True)
    action_api_id = Column(Integer, ForeignKey('action_api.id'))
    transform_api_id = Column(Integer, ForeignKey('transform_api.id'))
    name = Column(String(80), nullable=False)
    failure = Column(Boolean, default=False)
    description = Column(Text)
    schema = Column(JSONType)
    examples = Column(JSONType)


class Actionable(YamlConstructable):
    id = Column(Integer, primary_key=True)
    app_api_id = Column(Integer, ForeignKey('app_api.id'))
    name = Column(String(80), nullable=False)
    run = Column(Text, nullable=False)
    parameters = relationship('ParameterApi', cascade='all, delete-orphan')
    tags = relationship('ApiTag', secondary=action_api_tags_table)
    summary = Column(Text)
    description = Column(Text)
    external_docs = relationship('ExternalDoc', cascade='all, delete-orphan')
    deprecated = Column(Boolean)

    _action_type = 'not specified'

    _children = (
        YamlChild('returns', ReturnApi, expansion='name'),
        YamlChild('parameters', ParameterApi),
        YamlChild('external_docs', ExternalDoc)
    )

    def _id_string(self):
        return 'app {} {} {}'.format(self.app.name, self._action_type, self.name)

    #TODO: GOOD
    def validate_arguments(self, arguments, accumulator=None):
        api_dict = {}
        for param in self.parameters:
            api_dict[param.name] = param
        converted = {}
        seen_params = set()
        arg_names = [argument.name for argument in arguments] if arguments else []
        arguments_set = set(arg_names)
        errors = []
        for param_name, parameter in api_dict.items():
            try:
                argument = get_argument_by_name(arguments, param_name)
                if argument:
                    arg_val = argument.get_value(accumulator)
                    if accumulator or not argument.is_ref:
                        converted[param_name] = api_dict[param_name].validate(arg_val, self._id_string())
                elif 'default' in parameter.schema:
                    default_param = parameter.schema['default']
                    try:
                        default_param = api_dict[param_name].validate(default_param, self._id_string())
                    except InvalidArgument as e:
                        logger.warning(
                            'For {}: Default input {} (value {}) does not conform to schema. (Error: {})'
                            'Using anyways'.format(
                                self._id_string(),
                                param_name,
                                default_param,
                                format_exception_message(e)
                            )
                        )

                    converted[param_name] = default_param
                    arguments_set.add(param_name)
                elif parameter.required:
                    message = 'For {}: Parameter {} is not specified and has no default'.format(
                        self._id_string(),
                        param_name
                    )
                    logger.error(message)
                    raise InvalidArgument(message)
                else:
                    converted[param_name] = None
                    arguments_set.add(param_name)
                seen_params.add(param_name)
            except InvalidArgument as e:
                errors.append(e.message)
        if seen_params != arguments_set:
            message = 'For {}: Too many arguments. Extra arguments: {}'.format(
                self._id_string(),
                list(arguments_set - seen_params)
            )
            logger.error(message)
            errors.append(message)
        if errors:
            raise InvalidArgument('Invalid arguments', errors=errors)
        return converted

    def validate_api_parameters(self, action_func):
        seen = set()
        for parameter in self.parameters:
            if parameter.name in seen:
                raise InvalidApi('Duplicate parameter {} in api for {}'.format(
                    parameter.name,
                    self._id_string())
                )
            seen.add(parameter.name)

        method_params = Actionable._get_method_arguments(action_func)

        if not seen == set(method_params):
            message = self._generate_invalid_method_argument_message(method_params, seen)
            raise InvalidApi(message)

    def _generate_invalid_method_argument_message(self, method_params, seen):
        only_in_api = seen - set(method_params)
        only_in_definition = set(method_params) - seen
        message = 'Discrepancy between defined parameters in API and in method definition for {}.'.format(
            self._id_string()
        )
        if only_in_api:
            message += ' Only in API: {}.'.format(list(only_in_api))
        if only_in_definition:
            message += ' Only in definition: {}'.format(list(only_in_definition))
        return message

    @staticmethod
    def _get_method_arguments(action_func):
        if hasattr(action_func, '__arg_names'):
            method_params = list(action_func.__arg_names)
        else:
            method_params = get_function_arg_names(action_func)
        if method_params and method_params[0] == 'self':
            method_params.pop(0)
        return method_params

    def _get_func(self):
        raise NotImplemented


class ActionApi(Actionable, Execution_Base):
    __tablename__ = 'action_api'
    returns = relationship('ReturnApi', cascade='all, delete-orphan')
    default_return = Column(String(80))

    _action_type = 'action'

    def validate_api(self, defined_actions):
        if self.run not in defined_actions:
            raise InvalidApi('Action {} has "run" property {} which is not defined in App {}'.format(
                self.name,
                self.run,
                self.app.name)
            )
        self.validate_api_parameters(self._get_func())
        if self.default_return and not any(return_code.name == self.default_return for return_code in self.returns):
            raise InvalidApi(
                'Default return {} not in defined return codes {}'.format(
                    self.default_return,
                    [return_code.name for return_code in self.returns]
                )
            )

        self.validate_return_codes()

    def validate_return_codes(self):
        reserved = [return_code for return_code in self.returns if return_code in reserved_return_codes]
        if reserved:
            message = '{} has return codes {} which are reserved'.format(self._id_string(), reserved)
            logger.error(message)
            raise InvalidApi(message)

    def _get_func(self):
        from walkoff.appgateway import get_app_action
        return get_app_action(self.app.name, self.run)


class ConditionTransformApi(Actionable):
    data_in = Column(String(80), nullable=False)

    # TODO: DONE
    def validate_api(self, defined_actions):
        if self.run not in defined_actions:
            raise InvalidApi('{} has a "run" param {} which is not defined'.format(self._id_string(), self.run))

        self.validate_data_in_param()
        function_ = self._get_func()
        self.validate_api_parameters(function_)

    def validate_data_in_param(self):
        data_in_param = next((parameter for parameter in self.parameters if parameter.name == self.data_in), None)
        if data_in_param is None:
            raise InvalidApi(
                '{0} has a data_in param {1} for which it does not have a corresponding parameter'.format(
                    self._id_string(),
                    self.data_in
                )
            )
        elif not data_in_param.get('required', False):
            raise InvalidApi(
                '{0} has a data_in param {1} which is not marked as required in the api. '
                'Add "required: true" to parameter specification for {1}'.format(
                    self._id_string(),
                    self.data_in
                )
            )


class ConditionApi(ConditionTransformApi, Execution_Base):
    __tablename__ = 'condition_api'
    _action_type = 'condition'

    def _get_func(self):
        from walkoff.appgateway import get_condition
        return get_condition(self.app.name, self.run)


class TransformApi(ConditionTransformApi, Execution_Base):
    __tablename__ = 'transform_api'
    returns = relationship('ReturnApi', cascade='all, delete-orphan')

    _action_type = 'transform'

    def _get_func(self):
        from walkoff.appgateway import get_transform
        return get_transform(self.app.name, self.run)



class DeviceFieldApi(YamlConstructable, Execution_Base):
    __tablename__ = 'device_field_api'
    id = Column(Integer, primary_key=True)
    device_api_id = Column(Integer, ForeignKey('device_api.id'))
    required = Column(Boolean, default=False)
    name = Column(String(80))
    encrypted = Column(Boolean, default=False)
    placeholder = Column(String(80))
    example = Column(Text)
    schema = Column(JSONType)

    def validate(self, value, message_prefix):
        field_type = self.schema['type']
        field_api = deepcopy(self.schema)

        # Necessary for optional fields
        if 'required' not in field_api and (value == '' or value is None):
            return

        if 'required' in field_api:
            field_api.pop('required')
        if 'encrypted' in field_api:
            hide = True
            field_api.pop('encrypted')
        else:
            hide = False
        validate_primitive_parameter(value, field_api, field_type, message_prefix, hide_input=hide)

    def validate_api(self):
        if self.schema and 'default' in self.schema:
            message_prefix = 'App {0} device type {1}'.format(self.device.app.name, self.device.type)
            default_value = self.schema['default']
            try:
                self.validate(default_value, message_prefix)
            except InvalidArgument as e:
                logger.exception(
                    'For {0}: Default input {1} does not conform to schema. (Error: {2}) Using anyways'.format(
                        message_prefix,
                        self.name,
                        format_exception_message(e)
                    )
                )
                raise



class DeviceApi(YamlConstructable, Execution_Base):
    __tablename__ = 'device_api'
    id = Column(Integer, primary_key=True)
    app_api_id = Column(Integer, ForeignKey('app_api.id'))
    name = Column(String(80))
    type = Column(String(80))
    description = Column(Text)
    fields = relationship('DeviceFieldApi', cascade='all, delete-orphan', backpopulates='device')

    _children = (YamlChild('fields', DeviceFieldApi), )

    def _id_str(self):
        return 'Device type {} for app {}'.format(self.name, self.app.name)

    def validate_device_fields(self, device_fields_in, validate_required=True):
        message_prefix = self._id_str()

        for field_api in self.fields:
            if field_api.name not in device_fields_in and 'default' in field_api.schema:
                device_fields_in[field_api.name] = field_api.schema['default']

        if validate_required:
            required_in_api = {field.name for field in self.fields if field.required}
            field_names = set(device_fields_in)
            if required_in_api - field_names:
                message = '{} requires {} field but only got {}'.format(
                    message_prefix,
                    list(required_in_api),
                    list(field_names)
                )
                logger.error(message)
                raise InvalidArgument(message)

        device_fields_api_dict = {field.name: field for field in self.fields}

        for field_name, field_in in device_fields_in.items():
            if field_name in device_fields_api_dict:
                device_fields_api_dict[field_name].validate(field_in, message_prefix)
            else:
                message = '{} was passed field {} which is not defined in its API'.format(message_prefix, field_name)
                logger.warning(message)
                raise InvalidArgument(message)

        return device_fields_in

    def validate_api(self):
        for field in self.fields:
            field.validate_api()



class AppApi(YamlConstructable, Execution_Base):
    __tablename__ = 'app_api'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    info = relationship('AppInfo', uselist=False, cascade='all, delete-orphan')
    actions = relationship('ActionApi', cascade='all, delete-orphan', backpopulates='app')
    conditions = relationship('ConditionApi', cascade='all, delete-orphan', backpopulates='app')
    transforms = relationship('TransformApi', cascade='all, delete-orphan', backpopulates='app')
    devices = relationship('DeviceApi', cascade='all, delete-orphan', backpopulates='app')

    _children = (
        YamlChild('info', AppApiInfo),
        YamlChild('actions', ActionApi, expansion='name'),
        YamlChild('conditions', ConditionApi, expansion='name'),
        YamlChild('transforms', TransformApi, expansion='name'),
        YamlChild('devices', DeviceApi, expansion='name')
    )

    def validate_api(self):
        action_getters = (
            (self.actions, get_all_actions_for_app, ActionApi._action_type),
            (self.conditions, get_all_conditions_for_app, ConditionApi._action_type),
            (self.transforms, get_all_transforms_for_app, TransformApi._action_type),
        )
        for action_apis, getter, action_type in action_getters:
            actions_in_module = set(getter(self.name))
            actions_in_api = set()
            for action_api in action_apis:
                action_api.validate_api()
                actions_in_api.add(action_api.name)

            if actions_in_module != actions_in_api:
                logger.warning(
                    'App {0} has defined the following {1}s which do not have a corresponding API: {2}. '
                    'These {1} will not be usable until defined in the API'.format(
                        self.name,
                        action_type,
                        list(actions_in_module - actions_in_api)
                    )
                )
        for device in self.devices:
            device.validate_api()


def construct_app_api(spec, app_name, walkoff_schema_path, spec_url='', http_handlers=None):
    walkoff_resolver = validate_spec_json(
        spec,
        os.path.join(walkoff_schema_path),
        spec_url,
        http_handlers
    )
    dereference = partial(deref, resolver=walkoff_resolver)
    dereferenced_spec = dereference(spec)
    app = AppApi.from_api_yaml(dereferenced_spec, name=app_name)
    app.validate_api()
    return app
