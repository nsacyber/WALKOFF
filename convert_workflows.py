import json
import os
from copy import deepcopy


def convert_playbooks():
    for subdir, dir, files in os.walk("."):
        for file in files:
            if file.endswith('.playbook'):
                path = os.path.join(subdir, file)
                convert_playbook(path)


def convert_playbook(path):
    print("Processing {}".format(path))
    with open(path, "r") as f:
        playbook = json.load(f)
        for workflow in playbook['workflows']:
            convert_workflow(workflow)
    with open(path, "w") as f:
        json.dump(playbook, f, sort_keys=True, indent=4, separators=(',', ': '))


def convert_workflow(workflow):
    if 'next_steps' not in workflow:
        next_steps = []
        for step in workflow['steps']:
            next_steps_for_step = [convert_next_step_uids(next_step, step) for next_step in step.pop("next_steps", [])]
            next_steps.append(next_steps_for_step)
        workflow["next_steps"] = next_steps

    steps_copy = deepcopy(workflow['steps'])
    workflow['start'] = next((step['uid'] for step in steps_copy if step['name']==workflow['start']), workflow['start'])

    for step in workflow['steps']:
        if 'arguments' not in step:
            step['arguments'] = step.pop('inputs', [])
        step['arguments'] = [convert_arg(arg, steps_copy) for arg in step['arguments']]

    for next_step in workflow.get('next_steps', []):
        convert_next_step(next_step, steps_copy)


def convert_next_step_uids(next_step, step):
    next_step["source_uid"] = step["uid"]
    dst = next_step.pop("name")
    next_step["destination_uid"] = dst


def convert_next_step(next_step, steps_copy):
    if 'flags' in next_step:
        next_step['conditions'] = next_step.pop('flags')
    for condition in next_step.get('conditions', []):
        convert_condition(condition, steps_copy)


def convert_condition(condition, steps_copy):
    convert_all_condition_transform_arguments(steps_copy, condition)
    if 'app' not in condition:
        condition['app'] = 'Utilities'
    if 'filters' in condition:
        condition['transforms'] = condition.pop('filters')
    for transform in condition['transforms']:
        convert_transform(steps_copy, transform)


def convert_transform(steps_copy, transform):
    convert_all_condition_transform_arguments(steps_copy, transform)
    if 'app' not in transform:
        transform['app'] = 'Utilities'


def convert_all_condition_transform_arguments(steps_copy, condition_transform):
    if 'arguments' not in condition_transform:
        condition_transform['arguments'] = condition_transform.pop('args', [])
    condition_transform['arguments'] = [convert_arg(arg, steps_copy) for arg in condition_transform['arguments']]


def convert_arg(arg, steps):
    new_arg = {'name': arg['name']}
    new_arg.update(convert_arg_value(arg['value'], steps))
    return new_arg


def convert_arg_value(arg, steps):
    if arg.startswith('@'):
        reference_step_name = arg[1:]
        reference_step_uid = next((step['uid'] for step in steps if step['name'] == reference_step_name), None)
        if reference_step_uid is not None:
            return {'reference': reference_step_uid}
        else:
            print('reference {} cannot be converted from name to UID. Step UID not found'.format(arg))
            return {'reference': arg[1:]}
    else:
        return {'value': arg}


if __name__ == "__main__":
    convert_playbooks()
