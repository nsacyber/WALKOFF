from core import workflow as wf
import xml.etree.cElementTree as et

class Controller():
    def __init__(self):
        self.workflows = {}
        self.instances = {}
        self.tree = None

    def loadWorkflowsFromFile(self, path):
        self.tree = et.ElementTree(file=path)
        for workflow in self.tree.iter(tag="workflow"):
            name = workflow.get("name")
            self.workflows[name] = wf.Workflow(name=name, workflowConfig=workflow)

    def writeWorkflowToFile(self, workflow="", path=""):
        xml = self.workflows[workflow].toXML()