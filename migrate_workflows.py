import json
import os
from copy import deepcopy
from os.path import join

from six import string_types

from apps import cache_apps, is_app_action_bound
from apps.devicedb import device_db, App
from walkoff.config.config import walkoff_version, load_app_apis
from walkoff.core.helpers import get_app_action_api


def convert_playbooks():
    for subdir, dir, files in os.walk(join('.', 'data', 'workflows')):
        for file in files:
            if file.endswith('.playbook'):
                path = os.path.join(subdir, file)
                convert_playbook(path)


def convert_playbook(path):
    print('Converting {}'.format(path))
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
    actions_copy = deepcopy(workflow['actions'])
    if 'branches' not in workflow:
        create_branches(workflow, actions_copy)

    convert_workflow_start_uid(workflow, actions_copy)

    for action in workflow['actions']:
        if 'arguments' not in action:
            action['arguments'] = action.pop('inputs', [])
        convert_action(action, actions_copy)

    for branch in workflow.get('branches', []):
        convert_branch(branch, actions_copy)


def create_branches(workflow, actions_copy):
    branches = []
    for action in workflow['actions']:
        branch_for_action = [convert_branch_uids(branch, action, actions_copy) for branch in
                             action.pop('next_steps', [])]
        branches.extend(branch_for_action)
    workflow['branches'] = branches


def convert_workflow_start_uid(workflow, actions_copy):
    start_uid = next((action['uid'] for action in actions_copy if action['name'] == workflow['start']),
                     None)
    if start_uid is None:
        print('Invalid starting step {}!!'.format(workflow['start']))
    workflow['start'] = start_uid


def convert_action(action, actions_copy):
    action.pop('risk', None)
    if 'arguments' not in action:
        action['arguments'] = action.pop('inputs', [])
    action['arguments'] = [convert_arg(arg, actions_copy) for arg in action['arguments']]
    action['app_name'] = action.pop('app')
    action['action_name'] = action.pop('action')
    app_name = action['app_name']
    if app_name == 'HelloWorld':
        action['action_name'] = convert_hello_world_action_names(action['action_name'])

    if 'device' in action:
        convert_action_device(action)

    action.pop('widgets', None)


def convert_action_device(action):
    device_name = action.pop('device')
    action_run, _ = get_app_action_api(action['app_name'], action['action_name'])
    if is_app_action_bound(action['app_name'], action_run):
        device_id = convert_device_to_device_id(action['app_name'], device_name, action['action_name'])
        if device_id is not None:
            action['device_id'] = device_id


def convert_device_to_device_id(app_name, device_name, action_name):
    app = device_db.session.query(App).filter(App.name == app_name).first()
    generic_error_ending = ('Devices are new held in field named "device_id" and are referenced by id rather than name.'
                            ' This will need to be changed manually.')
    if app is not None:
        device = next((device for device in app.devices if device.name == device_name), None)
        if device is None:
            print('WARNING: In action {0}: No device with name of {1} found for app {2}. '
                  '{3}'.format(action_name, device_name, app_name, generic_error_ending))
            return None
        else:
            return device.id
    else:
        print('WARNING: In action {0}: No app {2} found in database. '
              '{3}'.format(action_name, device_name, app_name, generic_error_ending))
        return None


def convert_branch_uids(branch, action, actions_copy):
    branch['source_uid'] = action['uid']
    dst = branch.pop('name')
    dst_uid = next((action['uid'] for action in actions_copy if action['name'] == dst), None)
    if dst_uid is None:
        print('Destination of branch {} is invalid'.format(branch['uid']))
    branch['destination_uid'] = dst_uid
    return branch


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


def convert_hello_world_action_names(name):
    new_name = ''
    for letter in name:
        if letter.isupper():
            new_name += ' ' + letter.lower()
        else:
            new_name += letter
    return new_name


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
    cache_apps(join('.', 'apps'))
    load_app_apis()
    convert_playbooks()
