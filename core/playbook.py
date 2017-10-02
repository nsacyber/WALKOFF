from core.workflow import Workflow


class Playbook(object):
    def __init__(self, name, workflows):
        self.name = name
        # TODO: When playbook endpoints use UIDs, this should store UIDS
        self.workflows = {workflow.name: workflow for workflow in workflows}

    def add_workflow(self, workflow):
        self.workflows[workflow.name] = workflow

    def has_workflow_name(self, workflow_name):
        return workflow_name in self.workflows

    def has_workflow_uid(self, workflow_uid):
        return any(workflow.uid == workflow_uid for workflow in self.workflows.values())

    def get_workflow_by_name(self, workflow_name):
        try:
            return self.workflows[workflow_name]
        except KeyError:
            return None

    def get_workflow_by_uid(self, workflow_uid):
        return next((workflow for workflow in self.workflows.values() if workflow.uid == workflow_uid), None)

    def get_all_workflow_names(self):
        return list(self.workflows.keys())

    def get_all_workflow_uids(self):
        return [workflow.uid for workflow in self.workflows.values()]

    def get_all_workflows_as_json(self):
        return [workflow.as_json() for workflow in self.workflows.values()]

    def get_all_workflows_as_limited_json(self):
        return [{'name': workflow_names, 'uid': workflow.uid} for workflow_names, workflow in self.workflows.items()]

    def rename_workflow(self, old_name, new_name):
        if old_name in self.workflows:
            self.workflows[new_name] = self.workflows.pop(old_name)
            self.workflows[new_name].name = new_name

    def remove_workflow_by_name(self, workflow_name):
        if workflow_name in self.workflows:
            self.workflows.pop(workflow_name)

    def as_json(self):
        return {"name": self.name,
                "workflows": [workflow.as_json() for workflow in self.workflows.values()]}

    @staticmethod
    def from_json(json_in):
        return Playbook(name=json_in['name'],
                        workflows=[Workflow.from_json(workflow_json) for workflow_json in json_in['workflows']])