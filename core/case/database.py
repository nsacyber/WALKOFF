import json
from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

from core.config.paths import case_db_path

_Base = declarative_base()


class _CaseEventLink(_Base):
    __tablename__ = 'case_event'
    case_id = Column(Integer, ForeignKey('case.id'), primary_key=True)
    event_id = Column(Integer, ForeignKey('event.id'), primary_key=True)


class Case(_Base):
    """Case ORM for the events database
    """
    __tablename__ = 'case'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    note = Column(String)
    events = relationship('Event', secondary='case_event', lazy='dynamic')

    def as_json(self, with_events=True):
        """Gets the JSON representation of a Case object.
        
        Args:
            with_events (bool, optional): A boolean to determine whether or not the events of the Case object should be
                included in the output.
                
        Returns:
            The JSON representation of a Case object.
        """
        output = {'id': str(self.id),
                  'name': self.name,
                  'note': self.note}
        if with_events:
            output['events'] = [event.as_json() for event in self.events]
        return output


class Event(_Base):
    """ORM for an Event in the events database
    """
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
        """Gets the JSON representation of an Event object.
        
        Args:
            with_cases (bool, optional): A boolean to determine whether or not the cases of the event object should be
                included in the output.
                
        Returns:
            The JSON representation of an Event object.
        """
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
        """Factory method to construct an Event object.
        
        Args:
            sender (cls): A boolean to determine whether or not the events of the Case object should be
            included in the output.
            timestamp (str): A string representation of a timestamp
            entry_message (str): The message associated with the event
            entry_type (str): The type of event being logged (Workflow, NextStep, Flag, etc.)
            data (str): Extra information to be logged with the event
            
        Returns:
            An Event object.
        """
        return Event(type=entry_type,
                     timestamp=timestamp,
                     ancestry=','.join(map(str, sender.ancestry)),
                     message=entry_message,
                     data=data)


class CaseDatabase(object):
    """
    Wrapper for the SQLAlchhemy Case database object
    """
    def __init__(self):
        self.create()

    def create(self):
        """ Creates the database
        """
        self.engine = create_engine('sqlite:///' + case_db_path)
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()

        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = Session()

        _Base.metadata.bind = self.engine
        _Base.metadata.create_all(self.engine)

    def tear_down(self):
        """ Tears down the database
        """
        self.session.rollback()
        self.connection.close()
        self.engine.dispose()

    def add_cases(self, case_names):
        """ Adds empty cases to the database
        
        Args:
            case_names (list[str]): A list of case names to add
        """
        additions = [Case(name=case_name) for case_name in set(case_names)]
        self.session.add_all(additions)
        self.session.commit()

    def delete_cases(self, case_names):
        """ Removes cases to the database
        
        Args:
            case_names (list[str]): A list of case names to remove
        """
        if case_names:
            cases = self.session.query(Case).filter(Case.name.in_(case_names)).all()
            for case in cases:
                self.session.delete(case)  # There is a more efficient way to delete all items
            self.session.commit()

    def rename_case(self, old_case_name, new_case_name):
        """ Renames a case
        
        Args:
            old_case_name (str): The case to rename
            new_case_name (str): The case's new name
        """
        if old_case_name and new_case_name:
            case = self.session.query(Case).filter(Case.name == old_case_name).first()
            if case:
                case.name = new_case_name
                self.session.commit()

    def edit_case_note(self, case_name, note):
        """ Edits the note attached to a case
        
        Args:
            case_name (str): The case to edit
            note (str): The case's note
        """
        if case_name:
            case = self.session.query(Case).filter(Case.name == case_name).first()
            if case:
                case.note = note
                self.session.commit()

    def edit_event_note(self, event_id, note):
        """ Edits the note attached to an event
        
        Args:
            event_id (int): The id of the event
            note (str): The event's note
        """
        if event_id:
            event = self.session.query(Event).filter(Event.id == event_id).first()
            if event:
                event.note = note
                self.session.commit()

    def add_event(self, event, cases):
        """ Adds an event to some cases
        
        Args:
            event (cls): A core.case.callbacks._EventEntry object to add to the cases
            cases (list[str]): The cases to add the event to
        """
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
        """Gets the JSON representation of all the cases in the case database.
        
        Returns:
            The JSON representation of all Case objects without their events.
        """
        return {'cases': [case.as_json(with_events=False)
                          for case in self.session.query(Case).all()]}

    def event_as_json(self, event_id):
        """Gets the JSON representation of an event in the case database.
        
        Returns:
            The JSON representation of an Event object.
        """
        return self.session.query(Event).filter(Event.id == event_id).first().as_json()

    def case_events_as_json(self, case_name):
        """Gets the JSON representation of all the events in the case database.
        
        Returns:
            The JSON representation of all Event objects without their cases.
        """
        event_id = self.session.query(Case).filter(Case.name == case_name).first().id
        if event_id:
            result = [event.as_json()
                      for event in self.session.query(Event).join(Event.cases).filter(Case.id == event_id).all()]
            return result
        return {}


def get_case_db(_singleton=CaseDatabase()):
    """ Singleton factory which returns the case database"""
    return _singleton

case_db = get_case_db()


# Initialize Module
def initialize():
    """ Initializes the case database
    """
    _Base.metadata.drop_all()
    _Base.metadata.create_all()


# Teardown Module
def tear_down():
    """ Tears down the case database
    """
    case_db.session.close()
    case_db.transaction.rollback()
    case_db.connection.close()
    case_db.engine.dispose()
