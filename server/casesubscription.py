import json

from .database import db, Base
import core.case.subscription

class CaseSubscription(Base):
    __tablename__ = 'case_config'

    name = db.Column(db.String(255), nullable=False)
    subscription = db.Text()

    def __init__(self, name, subscription='{}'):
        self.name = name
        try:
            json.loads(subscription)
            self.subscription = subscription
        except:
            self.subscription = '{}'

    def as_json(self):
        return {"name": self.name,
                "subscriptions": json.loads(self.subscription)}

    @staticmethod
    def from_json(name, subscription_json):
        return CaseSubscription(name, subscription=json.dumps(subscription_json))
