import logging

from api_gateway.executiondb.action import (ActionApi, ActionApiSchema,
                                            Action, ActionSchema)
from api_gateway.executiondb.appapi import AppApi, AppApiSchema
from api_gateway.executiondb.branch import Branch, BranchSchema
from api_gateway.executiondb.condition import Condition, ConditionSchema
from api_gateway.executiondb.dashboard import (Dashboard, DashboardSchema,
                                               Widget, WidgetSchema)
from api_gateway.executiondb.global_variable import GlobalVariable, GlobalVariableSchema
from api_gateway.executiondb.parameter import (Parameter, ParameterSchema,
                                               ParameterApi, ParameterApiSchema)
from api_gateway.executiondb.returns import ReturnApi, ReturnApiSchema
from api_gateway.executiondb.transform import Transform, TransformSchema
from api_gateway.executiondb.trigger import Trigger, TriggerSchema
from api_gateway.executiondb.workflow import Workflow, WorkflowSchema
from api_gateway.executiondb.workflow_variable import WorkflowVariable, WorkflowVariableSchema
from api_gateway.executiondb.workflowresults import (NodeStatus, NodeStatusSchema,
                                                     WorkflowStatus, WorkflowStatusSchema)

# This could be done better with a metaclass which registers subclasses
_schema_lookup = {
    Action: ActionSchema,
    ActionApi: ActionApiSchema,
    AppApi: AppApiSchema,
    Branch: BranchSchema,
    Condition: ConditionSchema,
    Dashboard: DashboardSchema,
    Widget: WidgetSchema,
    GlobalVariable: GlobalVariableSchema,
    Parameter: ParameterSchema,
    ParameterApi: ParameterApiSchema,
    ReturnApi: ReturnApiSchema,
    Transform: TransformSchema,
    Trigger: TriggerSchema,
    Workflow: WorkflowSchema,
    WorkflowVariable: WorkflowVariableSchema,
    NodeStatus: NodeStatusSchema,
    WorkflowStatus: WorkflowStatusSchema
}

logger = logging.getLogger(__name__)


def dump_element(element):
    """Dumps an execution element

    Args:
        element (ExecutionElement): The element to dump

    Returns:
        dict: The serialized element
    """
    return _schema_lookup[element.__class__]().dump(element)
