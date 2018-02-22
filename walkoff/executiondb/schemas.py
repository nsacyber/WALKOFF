from .playbook import Playbook
from .workflow import Workflow
from .action import Action
from .position import Position
from .branch import Branch
from .conditionalexpression import ConditionalExpression, valid_operators
from .condition import Condition
from .transform import Transform
from .argument import Argument
import walkoff.executiondb.devicedb as devicedb
from marshmallow_sqlalchemy import ModelSchema, ModelSchemaOpts, field_for
from marshmallow import validates_schema, ValidationError, fields, post_dump, pre_dump, pre_load, post_load
from marshmallow.validate import OneOf
from six import with_metaclass
from marshmallow_sqlalchemy.schema import ModelSchemaMeta
import walkoff.executiondb.devicedb

'''
class ExecutionBaseSchemaMeta(ModelSchema):
    def __new__(mcs, name, bases, attrs):
        required_fields = attrs.get('__required_fields__', [])
        nested_fields = attrs.get('__nested_fields__', {})
        relationships = attrs.get('__relationships__', {})
        #print(required_fields)
        model = getattr(attrs.get('Meta', None), 'model', None)
        #print(model)
        if required_fields and model is not None:
            for required_field in required_fields:
                attrs[required_field] = field_for(model, required_field, required=True)
        for nested_field, nested_schema in nested_fields.items():
            attrs[nested_field] = fields.Nested(nested_schema, many=True, default=None)
        for relationship_field, relationship_schema in relationships.items():
            attrs[relationship_field] = fields.Nested(relationship_schema(), default=None)
        return super(ExecutionBaseSchemaMeta, mcs).__new__(mcs, name, bases, attrs)
'''


class ExecutionBaseSchema(ModelSchema):
    __skipvalues = (None, [], [{}])

    @post_dump
    def remove_skip_values(self, data):
        return {
            key: value for key, value in data.items()
            if value not in self.__skipvalues
        }

    def load(self, data, session=None, instance=None, *args, **kwargs):
        session = walkoff.executiondb.devicedb.device_db.session
        # Maybe automatically find and use instance if 'id' (or key) is passed
        return super(ExecutionBaseSchema, self).load(data, session=session, instance=instance, *args, **kwargs)


class ArgumentSchema(ExecutionBaseSchema):
    name = field_for(Argument, 'name', required=True)
    value = fields.Raw()

    # TODO: Validate selection is UUID or int
    class Meta:
        model = Argument

    @validates_schema
    def validate_argument(self, data):
        has_value = 'value' in data
        has_reference = 'reference' in data
        if (not has_value and not has_reference) or (has_value and has_reference):
            raise ValidationError('Arguments must have either a value or a reference.')


class ActionableSchema(ExecutionBaseSchema):
    app_name = fields.Str(required=True)
    action_name = fields.Str(required=True)
    arguments = fields.Nested(ArgumentSchema, many=True)


class TransformSchema(ActionableSchema):
    class Meta:
        model = Transform


class ConditionSchema(ActionableSchema):
    transforms = fields.Nested(TransformSchema, many=True)
    is_negated = field_for(Condition, 'is_negated', default=False)

    class Meta:
        model = Condition


class ConditionalExpressionSchema(ExecutionBaseSchema):
    conditions = fields.Nested(ConditionSchema, many=True)
    child_expressions = fields.Nested('self', many=True)
    operator = field_for(ConditionalExpression, 'operator', default='and', validates=OneOf(*valid_operators), missing='and')
    is_negated = field_for(ConditionalExpression, 'is_negated', default=False)

    class Meta:
        model = ConditionalExpression
        excludes = ('parent', )


class BranchSchema(ExecutionBaseSchema):
    source_id = field_for(Branch, 'source_id', required=True)
    destination_id = field_for(Branch, 'destination_id', required=True)
    condition = fields.Nested(ConditionalExpressionSchema())
    priority = field_for(Branch, 'priority', default=999)
    status = field_for(Branch, 'status', default='Success')

    class Meta:
        model = Branch


class PositionSchema(ExecutionBaseSchema):
    x = field_for(Position, 'x', required=True)
    y = field_for(Position, 'y', required=True)

    class Meta:
        model = Position


class ActionSchema(ActionableSchema):
    trigger = fields.Nested(ConditionalExpressionSchema())
    position = fields.Nested(PositionSchema())

    class Meta:
        model = Action


class WorkflowSchema(ExecutionBaseSchema):
    name = field_for(Workflow, 'name', required=True)
    start = field_for(Workflow, 'start', required=True)
    actions = fields.Nested(ActionSchema, many=True)
    branches = fields.Nested(BranchSchema, many=True)

    class Meta:
        model = Workflow
        exclude = ('playbook', )


class PlaybookSchema(ExecutionBaseSchema):
    name = field_for(Playbook, 'name', required=True)
    workflows = fields.Nested(WorkflowSchema, many=True)

    class Meta:
        model = Playbook

_schema_lookup = {
    Playbook: PlaybookSchema,
    Workflow: WorkflowSchema,
    Action: ActionableSchema,
    Branch: BranchSchema,
    ConditionalExpression: ConditionalExpressionSchema,
    Condition: ConditionSchema,
    Transform: TransformSchema,
    Position: PositionSchema,
    Argument: ArgumentSchema}


def dump_element(element):
    return _schema_lookup[element.__class__]().dump(element).data
