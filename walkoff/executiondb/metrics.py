from datetime import timedelta

from sqlalchemy import Column, Integer, ForeignKey, String, Float
from sqlalchemy.orm import relationship
from sqlalchemy_utils import UUIDType

from walkoff.executiondb import Execution_Base


class AppMetric(Execution_Base):
    """ORM for AppMetric, which stores metrics for Apps

    Attributes:
        id (int): ID of the AppMetric object
        app (str): The name of the App
        count (int): The number of times this App was used
        actions (list[ActionMetric]): A list of ActionMetrics for this AppMetric
    """
    __tablename__ = 'app_metric'

    id = Column(Integer, primary_key=True, autoincrement=True)
    app = Column(String, nullable=False)
    count = Column(Integer)
    actions = relationship('ActionMetric', cascade='all, delete, delete-orphan')

    def __init__(self, app, actions=None):
        self.app = app
        self.actions = actions if actions else []
        self.count = 0

    def get_action_by_id(self, action_id):
        """Gets an ActionMetric by its ID

        Args:
            action_id (int): The ID of the ActionMetric

        Returns:
            (ActionMetric): The ActionMetric if it exists in the list, else None
        """
        for action in self.actions:
            if action.action_id == action_id:
                return action
        return None

    def as_json(self):
        """Gets the JSON representation of the AppMetric

        Returns:
            (dict): The JSON representation of the AppMetric
        """
        ret = {"name": self.app,
               "count": self.count}
        actions_list = []
        for action in self.actions:
            actions_list.append(action.as_json())
        ret["actions"] = actions_list
        return ret


class ActionMetric(Execution_Base):
    """ORM for ActionMetric, which stores metrics for the App Actions

    Attributes:
        id (int): The ID of the ActionMetric
        action_id (UUID): The ID of the associated Action
        action_name (str): The name of the Action
        app_metric_id (int): The FK ID of the associated AppMetric
        action_statuses (list[ActionStatus]): A list of ActionStatus objects
    """
    __tablename__ = 'action_metric'

    id = Column(Integer, primary_key=True, autoincrement=True)
    action_id = Column(UUIDType(binary=False), nullable=False)
    action_name = Column(String(255), nullable=False)
    app_metric_id = Column(Integer, ForeignKey('app_metric.id'))
    action_statuses = relationship('ActionStatusMetric', cascade='all, delete, delete-orphan')

    def __init__(self, action_id, name, action_statuses=None):
        self.action_id = action_id
        self.action_name = name
        self.action_statuses = action_statuses if action_statuses else []

    def get_action_status(self, status):
        """Gets the ActionStatus by its status

        Args:
            status (str): The status to search by

        Returns:
            (ActionStatusMetric): The corresponding ActionStatusMetric
        """
        for action_status in self.action_statuses:
            if action_status.status == status:
                return action_status
        return None

    def as_json(self):
        """Gets the JSON representation of the ActionMetric object

        Returns:
            (dict): The JSON representation of the object
        """
        ret = {"name": self.action_name}
        for action_status in self.action_statuses:
            if action_status.status == "success":
                ret["success_metrics"] = action_status.as_json()
            else:
                ret["error_metrics"] = action_status.as_json()
        return ret


class ActionStatusMetric(Execution_Base):
    """ORM for the ActionStatusMetric, which keeps track of the status for each ActionMetric

    Attributes:
        id (int): The ID of the object
        status (str): The status of the Action
        count (int): The number of times this Action has been executed
        avg_time (float): The average time for each execution
        action_metric_id (int): The FK ID of the corresponding ActionMetric

    """
    __tablename__ = 'action_status_metric'

    id = Column(Integer, primary_key=True, autoincrement=True)
    status = Column(String(10))
    count = Column(Integer)
    avg_time = Column(Float)
    action_metric_id = Column(Integer, ForeignKey('action_metric.id'))

    def __init__(self, status, avg_time):
        self.status = status
        self.avg_time = avg_time
        self.count = 1

    def update(self, execution_time):
        """Updates the average execution time for the Action

        Args:
            execution_time (float): The execution time for this execution instance of the Action
        """
        self.count += 1
        self.avg_time = (self.avg_time + execution_time) / 2

    def as_json(self):
        """Gets the JSON representation of the object

        Returns:
            (dict): The JSON representation of the object
        """
        ret = {"count": self.count,
               "avg_time": str(timedelta(seconds=self.avg_time))}
        return ret


class WorkflowMetric(Execution_Base):
    """ORM for the WorkflowMetric, which keeps track of metrics related to Workflows

    Attributes:
        id (int): The ID of the WorkflowMetric
        workflow_id (UUID): The UUID of the corresponding Workflow
        workflow_name (str): The name of the corresponding Workflow
        count (int): The number of times this workflow has been executed
        avg_time (float): The average time for each execution of this Workflow
    """
    __tablename__ = 'workflow_metric'

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(UUIDType(binary=False), nullable=False)
    workflow_name = Column(String(255), nullable=False)
    count = Column(Integer)
    avg_time = Column(Float)

    def __init__(self, workflow_id, workflow_name, avg_time):
        self.workflow_id = workflow_id
        self.workflow_name = workflow_name
        self.avg_time = avg_time
        self.count = 1

    def update(self, execution_time):
        """Updates the average execution time for the Workflow

        Args:
            execution_time (float): The execution time for this execution instance of the Workflow
        """
        self.count += 1
        self.avg_time = (self.avg_time + execution_time) / 2

    def as_json(self):
        """Gets the JSON representation of the object

        Returns:
            (dict): The JSON representation of the object
        """
        ret = {"name": self.workflow_name,
               "count": self.count,
               "avg_time": str(timedelta(seconds=self.avg_time))}
        return ret
