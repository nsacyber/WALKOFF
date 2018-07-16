from sqlalchemy import Column, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EmailType

from walkoff.executiondb import Execution_Base
from collections import namedtuple

def filter_yaml_extensions(yaml):
    return {key: value for key, value in yaml.items() if not key.startswith('x-')}


YamlExpansionKey = namedtuple('YamlExpansionKey', ['key', 'field'])


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
    def from_api_yaml(cls, yaml, *additional_keys):
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
            for child in cls.__children:
                child.construct_child(filtered_yaml)
        if hasattr(cls, 'schema'):
            class_attrs = [field for field in vars(cls) if not field.startswith('__') and field != 'schema']
            filtered_yaml['schema'] = {key: value for key, value in filtered_yaml if key not in class_attrs}
        filtered_yaml.update(additional_keys)
        return cls(**filtered_yaml)


class AppApiContact(YamlConstructable, Execution_Base):
    __tablename__ = 'app_api_contact'
    id = Column(Integer, primary_key=True)
    info_id = Column(Integer, ForeignKey('app_api_info.id'))
    name = Column(String(80))
    url = Column(String(80))
    email = Column(EmailType)


class AppApiLicense(YamlConstructable, Execution_Base):
    __tablename__ = 'app_api_license'
    id = Column(Integer, primary_key=True)
    info_id = Column(Integer, ForeignKey('app_api_info.id'))
    name = Column(String(80), nullable=False)
    url = Column(String(80))


class AppApiTag(YamlConstructable, Execution_Base):
    __tablename__ = 'app_api_tag'
    id = Column(Integer, primary_key=True)
    info_id = Column(Integer, ForeignKey('app_api_info.id'))
    name = Column(String(80), nullable=False)
    description = Column(Text())
    external_docs = relationship('ExternalDoc', cascade='all, delete-orphan')

    # TODO: Reorganize so this class import doesn't cause circular import
    _children = (YamlChild('external_docs', 'PLUGIN HERE'), )


class AppApiInfo(YamlConstructable, Execution_Base):
    __tablename__ = 'app_api_info'
    id = Column(Integer, primary_key=True)
    app_api_id = Column(Integer, ForeignKey('app_api.id'))
    version = Column(String(20), nullable=False)
    title = Column(String(80), nullable=False)
    description = Column(Text())
    terms_of_service = Column(Text())
    tags = relationship('AppApiTag', cascade='all, delete-orphan')
    contact = relationship('AppApiContact', uselist=False, cascade='all, delete-orphan')
    license = relationship('AppApiLicense', uselist=False, cascade='all, delete-orphan')

    _children = (
        YamlChild('tags', AppApiTag),
        YamlChild('contact', AppApiContact), 
        YamlChild('license', AppApiLicense)
    )
