from core import workflow as wf
import xml.etree.cElementTree as et

class Controller():
    def __init__(self):
        self.workflows = {}
        self.instances = {}

    def loadWorkflowsFromFile(self, path):
        tree = et.ElementTree(file=path)
        for workflow in tree.iter(tag="workflow"):
            name = workflow.get("name")
            self.workflows[name] = wf.Workflow(workflow)