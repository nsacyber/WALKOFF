import os
import sys
import uuid

from walkoff import executiondb

sys.path.append(os.path.abspath('.'))
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.action import Action
from walkoff.executiondb.branch import Branch
from walkoff.executiondb.condition import Condition
from walkoff.executiondb.playbook import Playbook
from walkoff.executiondb.transform import Transform
from walkoff.executiondb.workflow import Workflow
from walkoff.executiondb.position import Position
from walkoff.executiondb.conditionalexpression import ConditionalExpression

down_version = "0.6.7"
up_version = "0.7.0"

downgrade_supported = False
upgrade_supported = True


def downgrade_playbook(playbook):
    print("Downgrade not supported")
    pass


def downgrade_workflow(workflow):
    pass


def upgrade_playbook(playbook):
    workflows = []
    for workflow in playbook['workflows']:
        workflows.append(upgrade_workflow(workflow))

    playbook_obj = Playbook(name=playbook['name'], workflows=workflows, id=playbook.get('uid', None))

    executiondb.execution_db.session.add(playbook_obj)
    executiondb.execution_db.session.commit()


def upgrade_workflow(workflow):
    actions = []
    action_map = {}
    for action in workflow['actions']:
        actions.append(convert_action(action, action_map))

    branches = []
    if 'branches' in workflow:
        for branch in workflow['branches']:
            branch_obj = convert_branch(branch, action_map)
            if branch_obj:
                branches.append(branch_obj)

    name = workflow['name'] if 'name' in workflow else None

    if 'start' not in workflow:
        start = actions[0].id
        print('WARNING: "start" is now a required field for workflows. Setting start for workflow {0} to {1}'.format(
            name, start))
    else:
        if workflow['start'] in action_map:
            start = action_map[workflow['start']]
        else:
            start = actions[0].id
            print('WARNING: "start" field does not refer to a valid action for workflow {0}. '
                  'Setting "start" to {1}'.format(name, start))

    workflow_obj = Workflow(name=name, actions=actions, branches=branches, start=start, id=workflow.get('uid', None))

    return workflow_obj


def convert_action(action, action_map):
    uid = action.pop('uid')
    try:
        action_id = uuid.UUID(uid)
        action_map[uid] = action_id
    except Exception:
        print("Action UID is not valid UUID, creating new UID")
        action_id = uuid.uuid4()
        action_map[uid] = action_id

    arguments = []
    if 'arguments' in action:
        for argument in action['arguments']:
            arguments.append(convert_arg(argument))

    trigger = None
    if 'triggers' in action and len(action['triggers']) > 0:
        trigger = ConditionalExpression()
        for trig in action['triggers']:
            trigger.conditions.append(convert_condition(trig))

    name = action['name'] if 'name' in action else action['action_name']
    device_id = action['device_id'] if 'device_id' in action else None

    x = None
    y = None
    if 'position' in action and action['position']:
        x = action['position']['x']
        y = action['position']['y']
    position = Position(x, y) if x and y else None

    action_obj = Action(id=action_id, app_name=action['app_name'], action_name=action['action_name'], name=name,
                        device_id=device_id, position=position, arguments=arguments, trigger=trigger)

    return action_obj


def convert_arg(arg):
    value = arg['value'] if 'value' in arg else None
    reference = arg['reference'] if 'reference' in arg else None
    selection = arg['selection'] if 'selection' in arg else None

    arg_obj = Argument(name=arg['name'], value=value, reference=reference, selection=selection)

    return arg_obj


def convert_condition(condition):
    arguments = []
    if 'arguments' in condition:
        for argument in condition['arguments']:
            arguments.append(convert_arg(argument))

    transforms = []
    if 'transforms' in condition:
        for transform in condition['transforms']:
            transforms.append(convert_transform(transform))

    condition_obj = Condition(app_name=condition['app_name'], action_name=condition['action_name'],
                              id=condition.get('uid', None), arguments=arguments, transforms=transforms)

    return condition_obj


def convert_transform(transform):
    arguments = []
    if 'arguments' in transform:
        for argument in transform['arguments']:
            arguments.append(convert_arg(argument))

    transform_obj = Transform(app_name=transform['app_name'], action_name=transform['action_name'],
                              id=transform.get('uid', None), arguments=arguments)

    return transform_obj


def convert_branch(branch, action_map):
    condition = None
    if 'conditions' in branch and len(branch['conditions']) > 0:
        condition = ConditionalExpression()
        for cond in branch['conditions']:
            condition.conditions.append(convert_condition(cond))

    status = branch['status'] if 'status' in branch else None
    priority = branch['priority'] if 'priority' in branch else 999

    if branch['source_uid'] in action_map:
        source_id = action_map[branch['source_uid']]
    else:
        print("Source ID not found in actions, skipping branch")
        return None

    if branch['destination_uid'] in action_map:
        destination_id = action_map[branch['destination_uid']]
    else:
        print("Destination ID not found in actions, skipping branch")
        return None

    branch_obj = Branch(source_id=source_id, destination_id=destination_id, status=status, condition=condition,
                        priority=priority)

    return branch_obj
