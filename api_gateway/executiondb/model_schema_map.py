from api_gateway.executiondb.parameter import Parameter
from api_gateway.executiondb.action import Action
from api_gateway.executiondb.branch import Branch
from api_gateway.executiondb.condition import Condition
from api_gateway.executiondb.position import Position
from api_gateway.executiondb.transform import Transform
from api_gateway.executiondb.trigger import Trigger
from api_gateway.executiondb.global_variable import GlobalVariable
from api_gateway.executiondb.workflow_variable import WorkflowVariable
from api_gateway.executiondb.workflow import Workflow
from api_gateway.executiondb.workflowresults import WorkflowStatus, ActionStatus

from api_gateway.executiondb.schemas import (ParameterSchema, ActionSchema, BranchSchema, ConditionSchema,
                                             PositionSchema, TransformSchema, TriggerSchema, GlobalVariableSchema,
                                             WorkflowVariableSchema, WorkflowSchema,
                                             WorkflowStatusSchema, ActionStatusSchema)

# This could be done better with a metaclass which registers subclasses
_schema_lookup = {
    Workflow: WorkflowSchema,
    Position: PositionSchema,
    Action: ActionSchema,
    Branch: BranchSchema,
    Parameter: ParameterSchema,
    Condition: ConditionSchema,
    Transform: TransformSchema,
    Trigger: TriggerSchema,
    WorkflowVariable: WorkflowVariableSchema,
    GlobalVariable: GlobalVariableSchema,
    ActionStatus: ActionStatusSchema,
    WorkflowStatus: WorkflowStatusSchema
}


def dump_element(element):
    """Dumps an execution element

    Args:
        element (ExecutionElement): The element to dump

    Returns:
        dict: The serialized element
    """
    return _schema_lookup[element.__class__]().dump(element)
