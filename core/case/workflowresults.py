import json
from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from core.case.database import Case_Base


class WorkflowResult(Case_Base):
    """Case ORM for the events database
    """
    __tablename__ = 'workflow'
    id = Column(Integer, primary_key=True)
    uid = Column(String)
    name = Column(String)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    status = Column(String)
    results = relationship("ActionResult", backref='workflow', lazy='dynamic')

    def __init__(self, uid, name):
        self.uid = uid
        self.name = name
        self.started_at = datetime.utcnow()
        self.status = 'running'

    def complete(self):
        self.completed_at = datetime.utcnow()
        self.status = 'completed'

    def as_json(self):
        ret = {"uid": self.uid,
               "name": self.name,
               "started_at": str(self.started_at),
               "status": self.status,
               "results": [result.as_json() for result in self.results]}
        if self.status == 'completed':
            ret["completed_at"] = str(self.completed_at)
        return ret

    def paused(self):
        self.status = 'paused'

    def resumed(self):
        self.status = 'running'

    def trigger_action_awaiting_data(self):
        self.status = 'awaiting_data'

    def trigger_action_executing(self):
        self.status = 'running'


class ActionResult(Case_Base):
    """ORM for an Event in the events database
    """
    __tablename__ = 'result'
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime)
    name = Column(String)
    result = Column(String)
    input = Column(String)
    type = Column(String)
    action = Column(String)
    app = Column(String)
    workflow_result_id = Column(Integer, ForeignKey('workflow.id'))

    def __init__(self, name, result, action_input, action_type, app, action):
        self.name = name
        self.result = result
        self.input = action_input
        self.type = action_type
        self.timestamp = datetime.utcnow()
        self.app = app
        self.action = action

    def as_json(self):
        return {"name": self.name,
                "app": self.app,
                "action": self.action,
                "result": json.loads(self.result),
                "input": json.loads(self.input),
                "type": self.type,
                "timestamp": str(self.timestamp)}
