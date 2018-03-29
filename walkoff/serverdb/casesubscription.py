import json

from sqlalchemy_utils import JSONType

from walkoff.extensions import db
from walkoff.serverdb.mixins import TrackModificationsMixIn


class CaseSubscription(db.Model, TrackModificationsMixIn):
    """
    The ORM for the case subscriptions configuration
    """
    __tablename__ = 'case_subscription'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    subscriptions = db.Column(JSONType)
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
            self.subscriptions = subscriptions
        except json.JSONDecodeError:
            self.subscriptions = '[]'

    def as_json(self):
        """ Gets the JSON representation of the CaseSubscription object.
        
        Returns:
            The JSON representation of the CaseSubscription object.
        """
        return {"id": self.id,
                "name": self.name,
                "subscriptions": self.subscriptions,
                "note": self.note}

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
