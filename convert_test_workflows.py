import json
import os

from tests.config import WORKFLOWS_PATH


def convert_playbooks():
    for subd, d, files in os.walk(WORKFLOWS_PATH):
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
    for workflow in playbook.get('workflows', []):
        convert_workflow(workflow)
    return playbook


def convert_workflow(workflow):
    convert_subelements(workflow, 'actions', convert_action)
    convert_subelements(workflow, 'branches', convert_branch)


def convert_subelements(root, element_name, converter):
    for element in root.get(element_name, []):
        converter(element)


def convert_action(action):
    triggers = action.pop('triggers', [])
    if triggers:
        action['trigger'] = {'operation': 'and', 'conditions': triggers}


def convert_branch(branch):
    conditions = branch.pop('conditions', [])
    if conditions:
        branch['condition'] = {'operation': 'and', 'conditions': conditions}


if __name__ == '__main__':
    convert_playbooks()
