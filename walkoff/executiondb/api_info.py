from sqlalchemy import Column, Integer, ForeignKey, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy_utils import EmailType

from walkoff.executiondb import Execution_Base

from .yamlconstructable import YamlChild, YamlConstructable
from .actionapi import ExternalDoc


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

    _children = (YamlChild('external_docs', ExternalDoc),)


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
