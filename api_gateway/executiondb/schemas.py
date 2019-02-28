from marshmallow import validates_schema, ValidationError, fields, post_dump, post_load, EXCLUDE
from marshmallow.validate import OneOf
from marshmallow_sqlalchemy import ModelSchema, field_for

from api_gateway.executiondb import ExecutionDatabase
from .action import Action
from .parameter import Parameter
from .branch import Branch
from .condition import Condition
from .workflow_variable import WorkflowVariable
from .global_variable import Global
# from .executionelement import ExecutionElement
# from .playbook import Playbook
from .position import Position
from .transform import Transform
from .trigger import Trigger
from .workflow import Workflow
from .dashboard import Dashboard, Widget


# TODO: use these when moving toward storing apis in database
class ExecutionBaseSchema(ModelSchema):
    """Base schema for the execution database.

    This base class adds functionality to strip null fields from serialized objects and attaches the
    execution_db.session on load
    """
    __skipvalues = (None, [], [{}])

    @post_dump
    def _do_post_dump(self, data):
        return self.remove_skip_values(data)

    def remove_skip_values(self, data):
        """Removes fields with empty values from data

        Args:
            data (dict): The data passed in

        Returns:
            (dict): The data with forbidden fields removed
        """
        return {
            key: value for key, value in data.items()
            if value not in self.__skipvalues
        }

    def load(self, data, session=None, instance=None, *args, **kwargs):
        session = ExecutionDatabase.instance.session
        # Maybe automatically find and use instance if 'id' (or key) is passed
        return super(ExecutionBaseSchema, self).load(data, session=session, instance=instance, *args, **kwargs)


class ExecutionElementBaseSchema(ExecutionBaseSchema):
    errors = fields.List(fields.String())


class PositionSchema(ExecutionBaseSchema):
    """Schema for positions
    """
    x = field_for(Position, 'x', required=True)
    y = field_for(Position, 'y', required=True)

    class Meta:
        model = Position
        unknown = EXCLUDE
        # exclude = ('_id',)


class WorkflowVariableSchema(ExecutionBaseSchema):
    """Schema for workflow variables
    """
    name = field_for(WorkflowVariable, 'name')
    value = field_for(WorkflowVariable, 'value', required=True)
    description = field_for(WorkflowVariable, 'description')

    class Meta:
        model = WorkflowVariable
        unknown = EXCLUDE


class GlobalSchema(ExecutionBaseSchema):
    """Schema for global variables
    """
    name = field_for(Global, 'name')
    value = field_for(Global, 'value', required=True)
    description = field_for(Global, 'description')

    class Meta:
        model = Global
        unknown = EXCLUDE


class WidgetSchema(ExecutionBaseSchema):
    """Schema for Dashboard Widgets"""

    name = field_for(Widget, 'name', required=True)
    type_ = field_for(Widget, 'type_', required=True)
    x = field_for(Widget, 'x', required=True)
    y = field_for(Widget, 'y', required=True)
    cols = field_for(Widget, 'cols', required=True)
    rows = field_for(Widget, 'rows', required=True)
    options = fields.Raw()

    class Meta:
        model = Widget
        exclude = ('dashboard',)
        unknown = EXCLUDE


class DashboardSchema(ExecutionBaseSchema):
    """Schema for Dashboards"""

    name = field_for(Dashboard, 'name')
    widgets = fields.Nested(WidgetSchema, many=True)

    class Meta:
        model = Dashboard
        unknown = EXCLUDE


class ParameterSchema(ExecutionElementBaseSchema):
    """The schema for arguments.

    This class handles constructing the argument specially so that either a reference or a value is always non-null,
    but never both.
    """
    name = field_for(Parameter, 'name', required=True)
    value = fields.Raw()
    reference = field_for(Parameter, 'reference', required=False)
    variant = field_for(Parameter, 'variant', required=False)

    class Meta:
        model = Parameter
        unknown = EXCLUDE

    @validates_schema
    def validate_argument(self, data):
        has_value = 'value' in data
        has_reference = 'reference' in data and bool(data['reference'])
        if (not has_value and not has_reference) or (has_value and has_reference):
            raise ValidationError('Parameters must have either a value or a reference.', ['value'])

    @post_load
    def make_instance(self, data):
        instance = self.instance or self.get_instance(data)
        if instance is not None:
            value = data.pop('value', None)
            reference = data.pop('reference', None)
            instance.update_value_reference(value, reference)
            for key, value in data.items():
                setattr(instance, key, value)
            return instance
        return self.opts.model(**data)


class ConditionSchema(ExecutionElementBaseSchema):
    """Schema for conditions
    """

    name = field_for(Condition, 'name', required=True)
    conditional = field_for(Condition, 'conditional', required=True)
    position = fields.Nested(PositionSchema())

    class Meta:
        model = Condition
        unknown = EXCLUDE


class TransformSchema(ExecutionElementBaseSchema):
    """Schema for transforms
    """
    
    name = field_for(Transform, 'name', required=True)
    transform = field_for(Transform, 'transform', required=True)
    parameter = fields.Nested(ParameterSchema())
    position = fields.Nested(PositionSchema())

    class Meta:
        model = Transform
        unknown = EXCLUDE


class TriggerSchema(ExecutionElementBaseSchema):
    """Schema for triggers
    """

    name = field_for(Trigger, 'name', required=True)
    trigger = field_for(Trigger, 'trigger', required=True)
    position = fields.Nested(PositionSchema())

    class Meta:
        model = Trigger
        unknown = EXCLUDE


class BranchSchema(ExecutionElementBaseSchema):
    """Schema for branches
    """
    source_id = field_for(Branch, 'source_id', required=True)
    destination_id = field_for(Branch, 'destination_id', required=True)

    class Meta:
        model = Branch
        unknown = EXCLUDE


class ActionSchema(ExecutionElementBaseSchema):
    """Schema for actions
    """
    app_name = fields.Str(required=True)
    action_name = fields.Str(required=True)
    name = field_for(Action, 'name', required=True)
    parameters = fields.Nested(ParameterSchema, many=True)
    priority = field_for(Action, 'priority', default=3)
    position = fields.Nested(PositionSchema())

    class Meta:
        model = Action
        unknown = EXCLUDE


class WorkflowSchema(ExecutionElementBaseSchema):
    """Schema for workflows
    """
    name = field_for(Workflow, 'name', required=True)
    start = field_for(Workflow, 'start', required=True)
    actions = fields.Nested(ActionSchema, many=True)
    branches = fields.Nested(BranchSchema, many=True)
    conditions = fields.Nested(ConditionSchema, many=True)
    transforms = fields.Nested(TransformSchema, many=True)
    triggers = fields.Nested(TriggerSchema, many=True)
    workflow_variables = fields.Nested(WorkflowVariableSchema, many=True)

    # TODO: determine if this is needed
    # exclude = ("is_valid",)
    # is_valid = field_for(Workflow, 'is_valid')

    class Meta:
        model = Workflow
        unknown = EXCLUDE
        # exclude = ('playbook',)


# class PlaybookSchema(ExecutionElementBaseSchema):
#     """Schema for playbooks
#     """
#     name = field_for(Playbook, 'name', required=True)
#     workflows = fields.Nested(WorkflowSchema, many=True)
#
#     class Meta:
#         model = Playbook
#         unknown = EXCLUDE



# This could be done better with a metaclass which registers subclasses
_schema_lookup = {
    # Playbook: PlaybookSchema,
    Workflow: WorkflowSchema,
    Position: PositionSchema,
    Action: ActionSchema,
    Branch: BranchSchema,
    Parameter: ParameterSchema,
    Condition: ConditionSchema,
    Transform: TransformSchema,
    Trigger: TriggerSchema}


def dump_element(element):
    """Dumps an execution element

    Args:
        element (ExecutionElement): The element to dump

    Returns:
        dict: The serialized element
    """
    return _schema_lookup[element.__class__]().dump(element)
