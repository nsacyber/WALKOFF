import json
import logging
from datetime import datetime

from sqlalchemy import Column, Integer, ForeignKey, String, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, scoped_session

import walkoff.config.config
import walkoff.config.paths
from walkoff.helpers import format_db_path
from walkoff.helpers import utc_as_rfc_datetime

logger = logging.getLogger(__name__)

Case_Base = declarative_base()


class _CaseEventLink(Case_Base):
    __tablename__ = 'case_event'
    case_id = Column(Integer, ForeignKey('case.id'), primary_key=True)
    event_id = Column(Integer, ForeignKey('event.id'), primary_key=True)


class Case(Case_Base):
    """Case ORM for the events database
    """
    __tablename__ = 'case'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    events = relationship('Event', secondary='case_event', lazy='dynamic')

    def as_json(self, with_events=True):
        """Gets the JSON representation of a Case object.
        
        Args:
            with_events (bool, optional): A boolean to determine whether or not the events of the Case object should be
                included in the output.
                
        Returns:
            The JSON representation of a Case object.
        """
        output = {'id': self.id,
                  'name': self.name}
        if with_events:
            output['events'] = [event.as_json() for event in self.events]
        return output


class Event(Case_Base):
    """ORM for an Event in the events database
    """
    __tablename__ = 'event'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    type = Column(String)
    originator = Column(String)
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
        output = {'id': self.id,
                  'timestamp': utc_as_rfc_datetime(self.timestamp),
                  'type': self.type,
                  'originator': str(self.originator),
                  'message': self.message if self.message is not None else '',
                  'note': self.note if self.note is not None else ''}
        if self.data is not None:
            try:
                output['data'] = json.loads(self.data)
            except (ValueError, TypeError):
                output['data'] = str(self.data)
        else:
            output['data'] = ''
        if with_cases:
            output['cases'] = [case.as_json(with_events=False) for case in self.cases]
        return output


class CaseDatabase(object):
    """Wrapper for the SQLAlchemy Case database object
    """

    __instance = None

    def __init__(self):
        self.engine = create_engine(
            format_db_path(walkoff.config.config.case_db_type, walkoff.config.paths.case_db_path))
        self.connection = self.engine.connect()
        self.transaction = self.connection.begin()

        Session = sessionmaker()
        Session.configure(bind=self.engine)
        self.session = scoped_session(Session)

        Case_Base.metadata.bind = self.engine
        Case_Base.metadata.create_all(self.engine)

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super(CaseDatabase, cls).__new__(cls)
        return cls.__instance

    def tear_down(self):
        """ Tears down the database
        """
        self.session.rollback()
        self.connection.close()
        self.engine.dispose()

    def rename_case(self, case_id, new_case_name):
        """ Renames a case
        
        Args:
            case_id (int): The case to rename
            new_case_name (str): The case's new name
        """
        case = self.session.query(Case).filter(Case.id == case_id).first()
        if case:
            case.name = new_case_name
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

    def add_event(self, event, case_ids):
        """ Adds an event to some cases
        
        Args:
            event (Event): An event to add to the cases
            case_ids (list[int]): The names of the cases to add the event to
        """
        event.originator = str(event.originator)
        cases = case_db.session.query(Case).filter(Case.id.in_(case_ids)).all()
        event.cases = cases
        self.session.add(event)
        self.session.commit()

    def cases_as_json(self):
        """Gets the JSON representation of all the cases in the case database.
        
        Returns:
            The JSON representation of all Case objects without their events.
        """
        return [case.as_json(with_events=False) for case in self.session.query(Case).all()]

    def event_as_json(self, event_id):
        """Gets the JSON representation of an event in the case database.
        
        Returns:
            The JSON representation of an Event object.
        """
        return self.session.query(Event).filter(Event.id == event_id).first().as_json()

    def case_events_as_json(self, case_id):
        """Gets the JSON representation of all the events in the case database.
        
        Returns:
            The JSON representation of all Event objects without their cases.
        """
        case = self.session.query(Case).filter(Case.id == case_id).first()
        if not case:
            raise Exception

        result = [event.as_json()
                  for event in case.events]
        return result


case_db = None


# Initialize Module
def initialize():
    """ Initializes the case database
    """
    Case_Base.metadata.drop_all()
    Case_Base.metadata.create_all()
