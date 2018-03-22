from walkoff.case.database import Event
from walkoff.helpers import json_dumps_or_string
from six import string_types


class CaseLogger(object):
    """A logger for cases

    Attributes:
        subscriptions: The subscriptions for all cases used by this logger
        _repository: The repository used to store cases and events

    Args:
        repository: The repository used to store cases and events
        subscriptions: The subscriptions for all cases used by this logger
    """
    def __init__(self, repository, subscriptions):
        self.subscriptions = subscriptions
        self._repository = repository

    def log(self, event, sender_id, data=None):
        """Log an event to the database if any cases have subscribed to it

        Args:
            event (WalkoffEvent): The event to log
            sender_id (UUID|str): The id of the entity which sent the event
            data (optional): Additional data to log for this event
        """
        if event.is_loggable():
            originator = str(sender_id)
            cases_to_add = self.subscriptions.get_cases_subscribed(originator, event.signal_name)
            if cases_to_add:
                event = self._create_event_entry(event, originator, data)
                self._repository.add_event(event, cases_to_add)

    def add_subscriptions(self, case_id, subscriptions):
        """Adds subscriptions to a case

        Args:
            case_id (int): The id of the case in the repository
            subscriptions (list[Subscription]): A list of subscriptions for this case
        """
        self.subscriptions.add_subscriptions(case_id, subscriptions)

    def update_subscriptions(self, case_id, subscriptions):
        """Updates the subscriptions to a case

        Args:
            case_id (int): The id of the case in the repository
            subscriptions (list[Subscription]): A list of subscriptions for this case
        """
        self.subscriptions.update_subscriptions(case_id, subscriptions)

    def delete_case(self, case_id):
        """Deletes a case from the subscriptions

        Args:
            case_id (int): The id of the case in the database to delete
        """
        self.subscriptions.delete_case(case_id)

    def clear_subscriptions(self):
        """Clears all subscriptions from the logger
        """
        self.subscriptions.clear()

    @staticmethod
    def _create_event_entry(event, originator, data):
        """Creates an event entry

        Args:
            event (WalkoffEvent): The event to log
            originator (str): The entity which originated the event
            data: Any additional data to log

        Returns:
            (Event): An event entry
        """
        data = CaseLogger._format_data(data)
        event = Event(
            type=event.event_type.name,
            originator=originator,
            message=event.value.message,
            data=data)
        return event

    @staticmethod
    def _format_data(data):
        """Formats additional data for an event entry

        Essentially this attempts to store a JSON version of the data and falls back on simply casting it to a string

        Args:
            data: The data to format

        Returns:
            (str): The formatted data
        """
        if data is None:
            data = ''
        elif not isinstance(data, string_types):
            data = json_dumps_or_string(data)
        return data
