from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType
from walkoff.executiondb import Execution_Base


'''
form of {<app>: {'actions': {<action>: {"success" : {'count': <count>
                                                     'avg_time': <average_execution_time>}
                                        "error": {'count': <count>
                                                  'avg_time': <average_execution_time>}
                 'count': <count>}}
'''


class AppMetric(Execution_Base):
    __tablename__ = 'app_metric'

    id = Column(Integer, primary_key=True, autoincrement=True)
    app_id = Column(UUIDType(binary=False), ForeignKey('app.id'))
    count = Column(Integer)
    actions = relationship('ActionMetric', cascade='all, delete, delete-orphan')

    def __init__(self, app_id, actions=None):
        self.app_id = app_id
        self.actions = actions if actions else []
        self.count = 0


class ActionMetric(Execution_Base):
    __tablename__ = 'action_metric'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    app_metric_id = Column(Integer, ForeignKey('app_metric.id'))

    # Need another table for success and error

    def __init__(self, app_metric_id):
        self.app_metric_id = app_metric_id
