import json
import logging

import walkoff.case.subscription
from walkoff.server.extensions import db
from walkoff.serverdb.mixins import TrackModificationsMixIn


class CaseSubscription(db.Model, TrackModificationsMixIn):
    """
    The ORM for the case subscriptions configuration
    """
    __tablename__ = 'case_subscription'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    subscriptions = db.Column(db.Text())
    note = db.Column(db.String)

    def __init__(self, name, subscriptions=None, note=''):
        """
        Constructs an instance of a CaseSubscription.
        
        Args:
            name (str): Name of the case subscription.
            subscriptions (list(dict)): A subscription JSON object.
            note (str, optional): Annotation of the event.
        """
        self.name = name
        self.note = note
        if subscriptions is None:
            subscriptions = []
        try:
            self.subscriptions = json.dumps(subscriptions)
        except json.JSONDecodeError:
            self.subscriptions = '[]'
        finally:
            subscriptions = {subscription['uid']: subscription['events'] for subscription in subscriptions}
            walkoff.case.subscription.add_cases({name: subscriptions})

    def as_json(self):
        """ Gets the JSON representation of the CaseSubscription object.
        
        Returns:
            The JSON representation of the CaseSubscription object.
        """
        return {"id": self.id,
                "name": self.name,
                "subscriptions": json.loads(self.subscriptions),
                "note": self.note}

    @staticmethod
    def update(case_name):
        """ Synchronizes the subscription from the subscription in memory in the core.
        
        Args:
            case_name (str): The name of case to synchronize.
        """
        case = CaseSubscription.query.filter_by(name=case_name).first()
        if case and case_name in walkoff.case.subscription.subscriptions:
            case_subs = walkoff.case.subscription.subscriptions[case_name]
            case.subscriptions = json.dumps([{'uid': uid, 'events': events} for uid, events in case_subs.items()])

    @staticmethod
    def from_json(name, subscription_json):
        """ Forms a CaseSubscription object from the provided JSON object.
        
        Args:
            name (str): The name of the case
            subscription_json (dict): A JSON representation of the subscription
            
        Returns:
            The CaseSubscription object parsed from the JSON object.
        """
        return CaseSubscription(name, subscriptions=subscription_json)

    @staticmethod
    def sync_to_subscriptions():
        """Sets the subscription in memory to that loaded into the database
        """
        logging.getLogger(__name__).debug('Syncing cases')
        cases = CaseSubscription.query.all()
        subscriptions = {case.name: {subscription['uid']: subscription['events']
                                     for subscription in json.loads(case.subscriptions)} for case in cases}
        walkoff.case.subscription.set_subscriptions(subscriptions)
