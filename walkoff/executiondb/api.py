import os
from functools import partial

from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from swagger_spec_validator.validator20 import deref

from walkoff.appgateway import get_all_actions_for_app, get_all_conditions_for_app, get_all_transforms_for_app
from walkoff.appgateway.validator import logger, validate_spec_json
from walkoff.executiondb import Execution_Base
from walkoff.executiondb.actionapi import ActionApi, ConditionApi, TransformApi, DeviceApi
from walkoff.executiondb.api_info import AppApiInfo
from walkoff.executiondb.yamlconstructable import YamlConstructable, YamlChild


class AppApi(YamlConstructable, Execution_Base):
    __tablename__ = 'app_api'
    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    info = relationship('AppApiInfo', uselist=False, cascade='all, delete-orphan')
    actions = relationship('ActionApi', cascade='all, delete-orphan', backref='app')
    conditions = relationship('ConditionApi', cascade='all, delete-orphan', backref='app')
    transforms = relationship('TransformApi', cascade='all, delete-orphan', backref='app')
    devices = relationship('DeviceApi', cascade='all, delete-orphan', backref='app')

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