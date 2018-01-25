import json
import os
import sys
from copy import deepcopy

sys.path.append(os.path.abspath('.'))
import walkoff.coredb.devicedb
from walkoff.coredb.argument import Argument
from walkoff.coredb.action import Action
from walkoff.coredb.branch import Branch
from walkoff.coredb.condition import Condition
from walkoff.coredb.playbook import Playbook
from walkoff.coredb.transform import Transform
from walkoff.coredb.workflow import Workflow
from walkoff.coredb.position import Position

# import walkoff.__version__ as walkoff_version

down_version = "0.4.2"
up_version = "0.5.0"

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

    playbook_obj = Playbook(name=playbook['name'], workflows=workflows)

    walkoff.coredb.devicedb.device_db.session.add(playbook_obj)
    walkoff.coredb.devicedb.device_db.session.commit()


def upgrade_workflow(workflow):
    actions = []
    for action in workflow['actions']:
        actions.append(convert_action(action))

    all_args = [argument for action in actions for argument in action.arguments]

    # Convert all references in arguments
    for argument in all_args:
        if argument.reference:
            for action in workflow['actions']:
                print("Arg ref: {}".format(argument.reference))
                print("Action prev id: {}".format(action['prev_id']))
                if argument.reference == action['prev_id']:
                    print("updating to: {}".format(action['id']))
                    argument.reference = action['id']
                    walkoff.coredb.devicedb.device_db.session.add(argument)
                    break

    branches = []
    if 'branches' in workflow:
        for branch in workflow['branches']:
            branches.append(convert_branch(branch, workflow['actions']))

    start = None
    if 'start' in workflow:
        for action in workflow['actions']:
            if action['prev_id'] == workflow['start']:
                start = action['id']

    name = workflow['name'] if 'name' in workflow else None
    workflow_obj = Workflow(name=name, actions=actions, branches=branches, start=start)

    walkoff.coredb.devicedb.device_db.session.add(workflow_obj)
    walkoff.coredb.devicedb.device_db.session.commit()

    for action in workflow_obj.actions:
        if action.templated:
            print(action.raw_representation)

    walkoff.coredb.devicedb.device_db.session.commit()

    return workflow_obj


def convert_action(action):
    action_copy = deepcopy(action)
    action_copy.pop("id", None)
    action_copy.pop("position", None)

    arguments = []
    if 'arguments' in action:
        for argument in action['arguments']:
            arguments.append(convert_arg(argument))

    triggers = []
    if 'triggers' in action:
        for trigger in action['triggers']:
            triggers.append(convert_condition(trigger))

    name = action['name'] if 'name' in action else None
    device_id = action['device_id'] if 'device_id' in action else None

    x = None
    y = None
    if 'position' in action and action['position']:
        x = action['position']['x']
        y = action['position']['y']
    position = Position(x, y) if x and y else None

    templated = action['templated'] if 'templated' in action else None

    action_obj = Action(app_name=action['app_name'], action_name=action['action_name'], name=name, device_id=device_id,
                        position=position, templated=templated, raw_representation=action_copy, arguments=arguments,
                        triggers=triggers)

    walkoff.coredb.devicedb.device_db.session.add(action_obj)
    walkoff.coredb.devicedb.device_db.session.commit()

    action['prev_id'] = action['id']
    action['id'] = action_obj.id

    return action_obj


def convert_arg(arg):
    value = arg['value'] if 'value' in arg else None
    reference = arg['reference'] if 'reference' in arg else None
    selection = arg['selection'] if 'selection' in arg else None

    arg_obj = Argument(name=arg['name'], value=value, reference=reference, selection=selection)
    walkoff.coredb.devicedb.device_db.session.add(arg_obj)
    walkoff.coredb.devicedb.device_db.session.commit()

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

    condition_obj = Condition(app_name=condition['app_name'], action_name=condition['action_name'], arguments=arguments,
                              transforms=transforms)

    walkoff.coredb.devicedb.device_db.session.add(condition_obj)
    walkoff.coredb.devicedb.device_db.session.commit()
    return condition_obj


def convert_transform(transform):
    arguments = []
    if 'arguments' in transform:
        for argument in transform['arguments']:
            arguments.append(convert_arg(argument))

    transform_obj = Transform(app_name=transform['app_name'], action_name=transform['action_name'], arguments=arguments)

    walkoff.coredb.devicedb.device_db.session.add(transform_obj)
    walkoff.coredb.devicedb.device_db.session.commit()
    return transform_obj


def convert_branch(branch, actions):
    conditions = []
    if 'conditions' in branch:
        for condition in branch['conditions']:
            conditions.append(convert_condition(condition))

    source_id = None
    destination_id = None
    status = branch['status'] if 'status' in branch else None

    for action in actions:
        if action['prev_id'] == branch['source_id']:
            source_id = action['id']
        if action['prev_id'] == branch['destination_id']:
            destination_id = action['id']

    if 'priority' in branch:
        branch_obj = Branch(source_id=source_id, destination_id=destination_id, status=status, conditions=conditions,
                            priority=branch['priority'])
    else:
        branch_obj = Branch(source_id=source_id, destination_id=destination_id, status=status, conditions=conditions)

    walkoff.coredb.devicedb.device_db.session.add(branch_obj)
    walkoff.coredb.devicedb.device_db.session.commit()
    return branch_obj
