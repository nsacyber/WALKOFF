import json
import os
from copy import deepcopy
from six import string_types
from core.config.config import walkoff_version

def convert_playbooks():
    for subdir, dir, files in os.walk('.'):
        for file in files:
            if file.endswith('.playbook'):
                path = os.path.join(subdir, file)
                convert_playbook(path)


def convert_playbook(path):
    print('Processing {}'.format(path))
    with open(path, 'r') as f:
        playbook = json.load(f)
        playbook['walkoff_version'] = walkoff_version
        for workflow in playbook['workflows']:
            convert_workflow(workflow)
    with open(path, 'w') as f:
        json.dump(playbook, f, sort_keys=True, indent=4, separators=(',', ': '))


def convert_workflow(workflow):
    if 'actions' not in workflow:
        workflow['actions'] = workflow.pop('steps')
    if 'branches' not in workflow:
        branches = []
        for action in workflow['actions']:
            next_action_for_action = [convert_branch_uids(branch, action) for branch in action.pop('next_steps', [])]
            branches.append(next_action_for_action)
        workflow['branches'] = branches

    actions_copy = deepcopy(workflow['actions'])
    workflow['start'] = next((step['uid'] for step in actions_copy if step['name'] == workflow['start']), 
                             workflow['start'])

    for action in workflow['actions']:
        if 'arguments' not in action:
            action['arguments'] = action.pop('inputs', [])
        action['arguments'] = [convert_arg(arg, actions_copy) for arg in action['arguments']]

        convert_action(action, actions_copy)
    for branch in workflow.get('branches', []):
        convert_branch(branch, actions_copy)


def convert_action(step, steps_copy):
    if 'arguments' not in step:
        step['arguments'] = step.pop('inputs', [])
    step['arguments'] = [convert_arg(arg, steps_copy) for arg in step['arguments']]
    if 'device' in step:
        print('Warning step {} contains a device. '
              'Devices are now held in "device_id" field and reference a device name, not id.')
    step.pop('widgets', None)


def convert_branch_uids(branch, action):
    branch['source_uid'] = action['uid']
    dst = branch.pop('name')
    branch['destination_uid'] = dst


def convert_branch(branch, actions_copy):
    if 'flags' in branch:
        branch['conditions'] = branch.pop('flags')
    for condition in branch.get('conditions', []):
        convert_condition(condition, actions_copy)


def convert_condition(condition, actions_copy):
    convert_all_condition_transform_arguments(actions_copy, condition)
    if 'app' not in condition:
        condition['app_name'] = 'Utilities'
    if 'action' in condition:
        condition['action_name'] = condition.pop('action')
    if 'filters' in condition:
        condition['transforms'] = condition.pop('filters')
    for transform in condition['transforms']:
        convert_transform(actions_copy, transform)


def convert_transform(actions_copy, transform):
    convert_all_condition_transform_arguments(actions_copy, transform)
    if 'app' not in transform:
        transform['app_name'] = 'Utilities'
    if 'action' in transform:
        transform['action_name'] = transform.pop('action')


def convert_all_condition_transform_arguments(actions_copy, condition_transform):
    if 'arguments' not in condition_transform:
        condition_transform['arguments'] = condition_transform.pop('args', [])
    condition_transform['arguments'] = [convert_arg(arg, actions_copy) for arg in condition_transform['arguments']]


def convert_arg(arg, steps):
    new_arg = {'name': arg['name']}
    new_arg.update(convert_arg_value(arg['value'], steps))
    return new_arg


def convert_arg_value(arg, steps):
    if isinstance(arg, string_types) and arg[0] == '@':
        reference_step_name = arg[1:]
        reference_step_uid = next((step['uid'] for step in steps if step['name'] == reference_step_name), None)
        if reference_step_uid is not None:
            return {'reference': reference_step_uid}
        else:
            print('reference {} cannot be converted from name to UID. Step UID not found'.format(arg))
            return {'reference': arg[1:]}
    else:
        return {'value': arg}


if __name__ == '__main__':
    convert_playbooks()
