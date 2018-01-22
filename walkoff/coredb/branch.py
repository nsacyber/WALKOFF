import logging
from functools import total_ordering

from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship, backref

from walkoff.coredb import Device_Base
from walkoff.events import WalkoffEvent
from walkoff.coredb.executionelement import ExecutionElement
from walkoff.coredb.condition import Condition
import walkoff.coredb.devicedb

logger = logging.getLogger(__name__)


@total_ordering
class Branch(ExecutionElement, Device_Base):
    __tablename__ = 'branch'
    id = Column(Integer, primary_key=True, autoincrement=True)
    _workflow_id = Column(Integer, ForeignKey('workflow.id'))
    source_id = Column(Integer, nullable=False)
    destination_id = Column(Integer, nullable=False)
    status = Column(String(80))
    conditions = relationship('Condition', backref=backref('_branch'), cascade='all, delete-orphan')
    priority = Column(Integer)

    def __init__(self, source_id, destination_id, status='Success', conditions=None, priority=999):
        """Initializes a new Branch object.
        
        Args:
            source_id (int): The ID of the source action that will be sending inputs to this Branch.
            destination_id (int): The ID of the destination action that will be returned if the conditions for this
                Branch are met.
            status (str, optional): Optional field to keep track of the status of the Branch. Defaults to
                "Success".
            conditions (list[Condition], optional): A list of Condition objects for the Branch object.
                Defaults to None.
            priority (int, optional): Optional priority parameter to specify which Branch in the Workflow's
                list of Branches should be executed if multiple have conditions resulting to True.
                Defaults to 999 (lowest priority).
        """
        ExecutionElement.__init__(self)
        self.source_id = source_id
        self.destination_id = destination_id
        self.status = status
        self.priority = priority

        self.conditions = []
        if conditions:
            self.conditions = conditions

    def __eq__(self, other):
        return self.source_id == other.source_id and self.destination_id == other.destination_id and \
               self.status == other.status and set(self.conditions) == set(other.conditions)

    def __lt__(self, other):
        return self.priority < other.priority

    def execute(self, data_in, accumulator):
        """Executes the Branch object, determining if this Branch should be taken.

        Args:
            data_in (): The input to the Condition objects associated with this Branch.
            accumulator (dict): The accumulated data from previous Actions.

        Returns:
            Destination UID for the next Action that should be taken, None if the data_in was not valid
                for this Branch.
        """
        if data_in is not None and data_in.status == self.status:
            if all(condition.execute(data_in=data_in.result, accumulator=accumulator) for condition in self.conditions):
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.BranchTaken)
                logger.debug('Branch is valid for input {0}'.format(data_in))
                return self.destination_id
            else:
                logger.debug('Branch is not valid for input {0}'.format(data_in))
                WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.BranchNotTaken)
                return None
        else:
            return None

    def update(self, data):
        self.source_id = data['source_id']
        self.destination_id = data['destination_id']
        self.status = data['status']
        self.priority = data['priority']

        if 'conditions' in data:
            conditions_seen = []
            for condition in data['conditions']:
                if 'id' in condition and condition['id']:
                    condition_obj = self.__get_condition_by_id(condition['id'])
                    condition_obj.update(condition)
                    conditions_seen.append(condition_obj.id)
                else:
                    if 'id' in condition:
                        condition.pop('id')
                    condition_obj = Condition(**condition)
                    self.conditions.append(condition_obj)
                    walkoff.coredb.devicedb.device_db.session.add(condition_obj)
                    walkoff.coredb.devicedb.device_db.session.commit()
                    conditions_seen.append(condition_obj.id)

            for condition in self.conditions:
                if condition.id not in conditions_seen:
                    walkoff.coredb.devicedb.device_db.session.delete(condition)
        else:
            self.conditions[:] = []

    def __get_condition_by_id(self, condition_id):
        for condition in self.conditions:
            if condition.id == condition_id:
                return condition
        return None
