from genericpath import isfile
from os import remove

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, func, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from core import config

_Base = declarative_base()


class Case_Event(_Base):
    __tablename__ = 'case_event'
    case_id = Column(Integer, ForeignKey('cases.id'), primary_key=True)
    event_id = Column(Integer, ForeignKey('event_log.id'), primary_key=True)


class Cases(_Base):
    __tablename__ = 'cases'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    events = relationship('EventLog', secondary='case_event', lazy='dynamic')


class EventLog(_Base):
    __tablename__ = 'event_log'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=func.now())
    type = Column(String)
    ancestry = Column(String)
    message = Column(String)
    cases = relationship('Cases', secondary='case_event', lazy='dynamic')

    @staticmethod
    def create(sender, entry_message, entry_type):
        return EventLog(type=entry_type, ancestry=','.join(map(str, sender.ancestry)), message=entry_message)


class CaseDatabase(object):
    def __init__(self):
        self.create()

    def create(self):
        self.engine = create_engine('sqlite:///' + config.case_db_path)
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()

        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = Session()

        _Base.metadata.bind = self.engine
        _Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.session.rollback()
        self.connection.close()
        self.engine.dispose()

    def register_events(self, case_names):
        self.session.add_all([Cases(name=case_name) for case_name in set(case_names)])
        self.session.commit()

    def add_event(self, event, cases):
        event_log = EventLog(type=event.type,
                                  ancestry=','.join(map(str, event.ancestry)),
                                  message=event.message)
        existing_cases = case_db.session.query(Cases).all()
        existing_case_names = [case.name for case in existing_cases]
        for case in cases:
            if case in existing_case_names:
                for case_elem in existing_cases:
                    if case_elem.name == case:
                        event_log.cases.append(case_elem)
            else:
                print("ERROR: Case is not tracked")
        self.session.add(event_log)
        self.session.commit()


case_db = CaseDatabase()


def initialize():
    if isfile(config.case_db_path):
        if config.reinitialize_case_db_on_startup:
            case_db.tearDown()
            remove(config.case_db_path)
            case_db.create()
    else:
        case_db.create()