import logging

from threading import Lock
from collections import namedtuple

logger = logging.getLogger(__name__)

Subscription = namedtuple('Subscription', ['id', 'events'])
"""A subscription for a single execution element
"""


class SubscriptionCache(object):
    """Cache for the subscriptions

    Structure is optimized for efficient lookup at the cost of efficient modification
    """
    def __init__(self):
        self._lock = Lock()
        self._subscriptions = {}

    def get_cases_subscribed(self, sender_id, event):
        with self._lock:
            return self._subscriptions.get(sender_id, {}).get(event, set())

    def update_subscriptions(self, case_id, case_subscriptions):
        """Updates the subscription cache for a case

        Note: We invert the structure of the cases from those in the serverdb for efficient lookup
        
        Args:
            case_id:
            case_subscriptions:

        Returns:

        """
        with self._lock:
            for case_subscription in case_subscriptions:
                sender_id = case_subscription.id
                if sender_id not in self._subscriptions:
                    self._subscriptions[sender_id] = {}
                for event in case_subscription.events:
                    if event in self._subscriptions[sender_id]:
                        self._subscriptions[sender_id][event].add(case_id)
                    else:
                        self._subscriptions[sender_id][event] = {case_id}

    def remove_case(self, case):
        with self._lock:
            for sender_id, events in self._subscriptions.items():
                for event, cases in events.items():
                    if case in cases:
                        cases.remove(case)
        self._clear_empty_subscriptions()

    def _clear_empty_subscriptions(self):
        with self._lock:
            self._subscriptions = {sender_id: {event: cases for event, cases in events.items() if cases}
                                   for sender_id, events in self._subscriptions.items()}

    def clear(self):
        with self._lock:
            self._subscriptions = {}
