import json

from .database import db, Base
import core.case.subscription


class CaseSubscription(Base):
    __tablename__ = 'case_subscription'

    name = db.Column(db.String(255), nullable=False)
    subscription = db.Column(db.Text())

    def __init__(self, name, subscription='{}'):
        self.name = name
        try:
            json.loads(subscription)
            self.subscription = subscription
        except:
            self.subscription = '{}'

    def as_json(self):
        return {"name": self.name,
                "subscription": json.loads(self.subscription)}

    @staticmethod
    def update(case_name):
        case = CaseSubscription.query.filter_by(name=case_name).first()
        if case:
            if case_name in core.case.subscription.subscriptions:
                case.subscription = json.dumps(core.case.subscription.subscriptions_as_json()[case_name])

    @staticmethod
    def from_json(name, subscription_json):
        return CaseSubscription(name, subscription=json.dumps(subscription_json))

    @staticmethod
    def sync_to_subscriptions():
        subscriptions = {case.name: core.case.subscription.CaseSubscriptions.from_json(json.loads(case.subscription))
                         for case in CaseSubscription.query.all()}
        core.case.subscription.set_subscriptions(subscriptions)

