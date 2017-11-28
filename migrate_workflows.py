import json
import os
from copy import deepcopy

from six import string_types

from apps.devicedb import device_db, App
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
        if 'walkoff_version' not in playbook:
            playbook['walkoff_version'] = walkoff_version
            for workflow in playbook['workflows']:
                convert_workflow(workflow)
    with open(path, 'w') as f:
        json.dump(playbook, f, sort_keys=True, indent=4, separators=(',', ': '))


def convert_workflow(workflow):
    workflow.pop('accumulated_risk', None)
    if 'actions' not in workflow:
        workflow['actions'] = workflow.pop('steps')
    if 'branches' not in workflow:
        branches = []
        for action in workflow['actions']:
            next_action_for_action = [convert_branch_uids(branch, action) for branch in action.pop('next_steps', [])]
            branches.append(next_action_for_action)
        workflow['branches'] = branches

    actions_copy = deepcopy(workflow['actions'])
    workflow['start'] = next((action['uid'] for action in actions_copy if action['name'] == workflow['start']),
                             workflow['start'])

    for action in workflow['actions']:
        if 'arguments' not in action:
            action['arguments'] = action.pop('inputs', [])
        action['arguments'] = [convert_arg(arg, actions_copy) for arg in action['arguments']]

        convert_action(action, actions_copy)
    for branch in workflow.get('branches', []):
        convert_branch(branch, actions_copy)


def convert_action(action, actions_copy):
    action.pop('risk', None)
    if 'arguments' not in action:
        action['arguments'] = action.pop('inputs', [])
    action['arguments'] = [convert_arg(arg, actions_copy) for arg in action['arguments']]
    if 'device' in action:
        device_name = action.pop('device')
        device_id = convert_device_to_device_id(action['app'], device_name, action['action'])
        if device_id is not None:
            action['device_id'] = device_id
    action.pop('widgets', None)


def convert_device_to_device_id(app_name, device_name, action_name):
    app = device_db.session.query(App).filter(App.name == app_name).first()
    generic_error_ending = ('Devices are new held in field named "device_id" and are referenced by id rather than name.'
                            ' This will need to be changed manually.')
    if app is not None:
        device = next((device for device in app.devices if device.name == device_name), None)
        if device is not None:
            print('WARNING: In action {0}: No device with name of {1} found for app {2}. '
                  '{3}'.format(action_name, device_name, app_name, generic_error_ending))
            return None
        else:
            return device.id
    else:
        print('WARNING: In action {0}: No app {2} found in database. '
              '{3}'.format(action_name, device_name, app_name, generic_error_ending))
        return None


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


def convert_arg(arg, actions):
    new_arg = {'name': arg['name']}
    new_arg.update(convert_arg_value(arg['value'], actions))
    return new_arg


def convert_arg_value(arg, actions):
    if isinstance(arg, string_types) and arg[0] == '@':
        reference_action_name = arg[1:]
        reference_action_uid = next((action['uid'] for action in actions if action['name'] == reference_action_name),
                                    None)
        if reference_action_uid is not None:
            return {'reference': reference_action_uid}
        else:
            print('reference {} cannot be converted from name to UID. Action UID not found'.format(arg))
            return {'reference': arg[1:]}
    else:
        return {'value': arg}


if __name__ == '__main__':
    convert_playbooks()
