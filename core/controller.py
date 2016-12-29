from core import workflow as wf
from core import config

import xml.etree.cElementTree as et

class Controller(object):
    def __init__(self):
        self.workflows = {}
        self.instances = {}
        self.tree = None

    def loadWorkflowsFromFile(self, path):
        self.tree = et.ElementTree(file=path)
        for workflow in self.tree.iter(tag="workflow"):
            name = workflow.get("name")
            self.workflows[name] = wf.Workflow(name=name, workflowConfig=workflow)
        self.addChildWorkflows()

    def addChildWorkflows(self):
        for workflow in self.workflows:
            children = self.workflows[workflow].options.children
            for child in children:
                if child in self.workflows:
                    children[child] = self.workflows[child]

    def createWorkflowFromTemplate(self, name="emptyWorkflow"):
        self.loadWorkflowsFromFile(path = config.templatesPath + name + ".workflow")

    def removeWorkflow(self, name=""):
        if name in self.workflows:
            del self.workflows[name]
            return True
        return False

    def updateWorkflowName(self, oldName="", newName=""):
        self.workflows[newName] = self.workflows.pop(oldName)
        self.workflows[newName].name = newName

    def writeWorkflowToFile(self, workflow="", path=""):
        xml = self.workflows[workflow].toXML()