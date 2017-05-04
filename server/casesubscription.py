import json
import logging

from .database import db, Base
import core.case.subscription


class CaseSubscription(Base):
    """
    The ORM for the case subscriptions configuration
    """
    __tablename__ = 'case_subscription'

    name = db.Column(db.String(255), nullable=False)
    subscription = db.Column(db.Text())

    def __init__(self, name, subscription='{}'):
        """
        Constructs an instance of a CaseSubscription
        Args:
            name (str): Name of the case subscription
            subscription (str): A string of the JSON representation of the subscription
        """
        self.name = name
        try:
            json.loads(subscription)
            self.subscription = subscription
        except:
            self.subscription = '{}'

    def as_json(self):
        """ Gets the JSON representation of all the CaseSubscription object.
        Returns:
            The JSON representation of the CaseSubscription object.
        """
        return {"name": self.name,
                "subscription": json.loads(self.subscription)}

    @staticmethod
    def update(case_name):
        """ Synchronizes the subscription from the subscription in memory in the core
        Args:
            case_name (str): The name of case to synchronize
        """
        case = CaseSubscription.query.filter_by(name=case_name).first()
        if case:
            if case_name in core.case.subscription.subscriptions:
                case.subscription = json.dumps(core.case.subscription.subscriptions_as_json()[case_name])

    @staticmethod
    def from_json(name, subscription_json):
        """ Forms a CaseSubscription object from the provided JSON object.
        Args:
            name (str): The name of the case
            subscription_json (dict): A JSON representation of the subscription
        Returns:
            The CaseSubscription object parsed from the JSON object.
        """
        return CaseSubscription(name, subscription=json.dumps(subscription_json))

    @staticmethod
    def sync_to_subscriptions():
        """Sets the subscription in memory to that loaded into the database
        """
        logging.getLogger(__name__).debug('Syncing cases')
        subscriptions = {case.name: core.case.subscription.CaseSubscriptions.from_json(json.loads(case.subscription))
                         for case in CaseSubscription.query.all()}
        core.case.subscription.set_subscriptions(subscriptions)

