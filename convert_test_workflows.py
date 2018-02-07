import os
import json
from uuid import uuid4
from tests.config import test_workflows_path


def convert_playbooks():
    for subd, d, files in os.walk(test_workflows_path):
        for f in files:
            if f.endswith('.playbook'):
                path = os.path.join(subd, f)
                with open(path, 'r') as playbook_file:
                    print(playbook_file)
                    playbook = convert_playbook(json.load(playbook_file))
                with open(path, 'w') as playbook_file:
                    print(playbook)
                    playbook_file.write(json.dumps(playbook, sort_keys=True, indent=4, separators=(',', ': ')))


def convert_playbook(playbook):
    convert_id(playbook)
    for workflow in playbook.get('workflows', []):
        convert_workflow(workflow)
    return playbook


def convert_workflow(workflow):
    convert_id(workflow)
    action_id_map = {}
    for action in workflow.get('actions', []):
        old_id, new_id = convert_id(action)
        action_id_map[old_id] = new_id
    convert_subelements(workflow, 'actions', convert_action, action_id_map)
    convert_subelements(workflow, 'branches', convert_branch, action_id_map)
    convert_or_create_id(workflow, 'start', action_id_map)


def convert_subelements(root, element_name, converter, action_id_map):
    for element in root.get(element_name, []):
        converter(element, action_id_map)


def convert_action(action, action_id_map):
    convert_subelements(action, 'triggers', convert_condition, action_id_map)
    convert_all_arguments(action, action_id_map)


def convert_branch(branch, action_id_map):
    convert_id(branch)
    for id_ in ('destination_id', 'source_id'):
        convert_or_create_id(branch, id_, action_id_map)


def convert_condition(condition, action_id_map):
    convert_id(condition)
    convert_subelements(condition, 'transforms', convert_transforms, action_id_map)
    convert_all_arguments(condition, action_id_map)


def convert_transforms(transform, action_id_map):
    convert_id(transform)
    convert_all_arguments(transform, action_id_map)


def convert_all_arguments(root, action_id_map):
    convert_subelements(root, 'arguments', convert_argument, action_id_map)


def convert_argument(argument, action_id_map):
    convert_or_create_id(argument, 'reference', action_id_map)


def convert_or_create_id(json_in, param, action_id_map):
    if param in json_in:
        json_in[param] = action_id_map.get(json_in[param], str(uuid4()))


def convert_id(json_in):
    if 'id' in json_in:
        old_id = json_in['id']
        json_in['id'] = str(uuid4())
        return old_id, json_in['id']
    return None, None

if __name__ == '__main__':
    convert_playbooks()