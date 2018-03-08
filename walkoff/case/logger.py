from walkoff.case.subscription import SubscriptionCache
import json
from walkoff.case.database import Event


class CaseLogger(object):
    def __init__(self, repository, subscriptions=None):
        self.subscriptions = subscriptions or SubscriptionCache()
        self._repository = repository

    def log(self, event, sender_id, data=None):
        if event.signal.is_loggable:
            originator = sender_id
            cases_to_add = self.subscriptions.get_cases_subscribed(originator, event.signal.name)
            if cases_to_add:
                event = self._create_event_entry(event, originator, data)
                self._repository.add_event(event, cases_to_add)

    def add_subscriptions(self, case_id, subscriptions):
        self.subscriptions.add_subscriptions(case_id, subscriptions)

    def update_subscriptions(self, case_id, subscriptions):
        self.subscriptions.update_subscriptions(case_id, subscriptions)

    def delete_case(self, case_id):
        self.subscriptions.delete_case(case_id)

    def clear_subscriptions(self):
        self.subscriptions.clear()

    @staticmethod
    def _create_event_entry(event, originator, data):
        data = CaseLogger._format_data(data)
        event = Event(
            type=event.event_type.name,
            originator=originator,
            message=event.signal.message,
            data=data)
        return event

    @staticmethod
    def _format_data(data):
        if data is None:
            data = ''
        elif isinstance(data, dict):
            try:
                data = json.dumps(data)
            except TypeError:
                data = str(data)
        return data
