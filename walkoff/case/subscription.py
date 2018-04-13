import logging
from collections import namedtuple
from threading import RLock

logger = logging.getLogger(__name__)

"""A subscription for a single execution element"""
Subscription = namedtuple('Subscription', ['id', 'events'])


class SubscriptionCache(object):
    """Cache for case subscriptions. Structure is optimized for efficient lookup at the cost of efficient
        modification"""

    def __init__(self):
        self._lock = RLock()
        self._subscriptions = {}

    def get_cases_subscribed(self, sender_id, event):
        """Gets the cases which are subscribed a given sender and event

        Args:
            sender_id (UUID): The id of the sender
            event (WalkoffEvent): The event of the sender

        Returns:
            (list[Case]): The list of Cases which are subscribed to a given sender and event
        """
        with self._lock:
            return self._subscriptions.get(sender_id, {}).get(event, set())

    def add_subscriptions(self, case_id, case_subscriptions):
        """Adds a case's subscriptions to the cache

        Args:
            case_id (int): The id of the case
            case_subscriptions (list[Subscription]): The subscriptions for this case
        """
        with self._lock:
            self._create_or_update_subscriptions(case_id, case_subscriptions)

    def update_subscriptions(self, case_id, subscriptions):
        """Updates the subscription cache for a case

        Args:
            case_id (int): The id of the case
            subscriptions (list[Subscription]): The new subscriptions for this case
        """
        with self._lock:
            self.delete_case(case_id)
            self._create_or_update_subscriptions(case_id, subscriptions)

    def _create_or_update_subscriptions(self, case_id, subscriptions):
        for case_subscription in subscriptions:
            sender_id = case_subscription.id
            if sender_id not in self._subscriptions:
                self._subscriptions[sender_id] = {}
            for event in case_subscription.events:
                if event in self._subscriptions[sender_id]:
                    self._subscriptions[sender_id][event].add(case_id)
                else:
                    self._subscriptions[sender_id][event] = {case_id}

    def delete_case(self, case_id):
        """Deletes all the subscriptions for a case

        Args:
            case_id (int): The id of the case
        """

        with self._lock:
            for sender_id, events in self._subscriptions.items():
                for event, cases in events.items():
                    if case_id in cases:
                        cases.remove(case_id)
            self._clear_empty_subscriptions()

    def _clear_empty_subscriptions(self):
        with self._lock:
            self._subscriptions = {sender_id: {event: cases for event, cases in events.items() if cases}
                                   for sender_id, events in self._subscriptions.items()}

    def clear(self):
        """Clears all the subscriptions for all cases"""
        with self._lock:
            self._subscriptions = {}
