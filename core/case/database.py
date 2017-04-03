from os import remove
import json
from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session

from core.config.paths import case_db_path

_Base = declarative_base()


class _Case_Event(_Base):
    __tablename__ = 'case_event'
    case_id = Column(Integer, ForeignKey('case.id'), primary_key=True)
    event_id = Column(Integer, ForeignKey('event.id'), primary_key=True)


class Case(_Base):
    __tablename__ = 'case'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    note = Column(String)
    events = relationship('Event', secondary='case_event', lazy='dynamic')

    def as_json(self, with_events=True):
        output = {'id': str(self.id),
                  'name': self.name,
                  'note': self.note}
        if with_events:
            output['events'] = [event.as_json() for event in self.events]
        return output


class Event(_Base):
    __tablename__ = 'event'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow())
    type = Column(String)
    ancestry = Column(String)
    message = Column(String)
    note = Column(String)
    data = Column(String)
    cases = relationship('Case', secondary='case_event', lazy='dynamic')

    def as_json(self, with_cases=False):
        output = {'id': str(self.id),
                  'timestamp': str(self.timestamp),
                  'type': self.type,
                  'ancestry': self.ancestry,
                  'message': self.message,
                  'data': self.data,
                  'note': self.note}
        if self.data:
            try:
                output['data'] = json.loads(self.data)
            except (ValueError, TypeError):
                output['data'] = self.data
        else:
            output['data'] = ''
        if with_cases:
            output['cases'] = [case.as_json() for case in self.cases]
        return output

    @staticmethod
    def create(sender, timestamp, entry_message, entry_type, data=''):
        return Event(type=entry_type,
                     timestamp=timestamp,
                     ancestry=','.join(map(str, sender.ancestry)),
                     message=entry_message,
                     data=data)


class CaseDatabase(object):
    def __init__(self):
        self.create()

    def create(self):
        self.engine = create_engine('sqlite:///' + case_db_path)
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()

        # Session = sessionmaker()
        # Session.configure(bind=self.engine)
        # self.session = Session()
        session_factory = sessionmaker(bind=self.engine)
        self.session = scoped_session(session_factory)

        _Base.metadata.bind = self.engine
        _Base.metadata.create_all(self.engine)

    def tearDown(self):
        self.session.rollback()
        self.connection.close()
        self.engine.dispose()

    def register_events(self, case_names):
        additions = [Case(name=case_name) for case_name in set(case_names)]
        self.session.add_all(additions)
        self.session.commit()

    def delete_cases(self, case_names):
        if case_names:
            cases = self.session.query(Case).filter(Case.name.in_(case_names)).all()
            for case in cases:
                self.session.delete(case)  # There is a more efficient way to delete all items
            self.session.commit()

    def rename_case(self, old_case_name, new_case_name):
        if old_case_name and new_case_name:
            case = self.session.query(Case).filter(Case.name == old_case_name).first()
            if case:
                case.name = new_case_name
                self.session.commit()

    def edit_case_note(self, case_name, note):
        if case_name:
            case = self.session.query(Case).filter(Case.name == case_name).first()
            if case:
                case.note = note
                self.session.commit()

    def edit_event_note(self, event_id, note):
        if event_id:
            event = self.session.query(Event).filter(Event.id == event_id).first()
            if event:
                event.note = note
                self.session.commit()

    def add_event(self, event, cases):
        event_log = Event(type=event.type,
                          timestamp=event.timestamp,
                          ancestry=','.join(map(str, event.ancestry)),
                          message=event.message,
                          data=event.data)
        existing_cases = case_db.session.query(Case).all()
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

    def cases_as_json(self):
        return {'cases': [case.as_json(with_events=False)
                          for case in self.session.query(Case).all()]}

    def event_as_json(self, event_id):
        return self.session.query(Event).filter(Event.id == event_id).first().as_json()

def get_case_db(_singleton = CaseDatabase()):
    return _singleton

case_db = get_case_db()

# Initialize Module
def initialize():
#     case_db.tearDown()
#     remove(case_db_path)
#     case_db.create()
    _Base.metadata.drop_all()
    _Base.metadata.create_all()
    pass

# Teardown Module
def tearDown():
    # case_db.session.close()
    # case_db.transaction.rollback()
    # case_db.connection.close()
    # case_db.engine.dispose()
    pass

