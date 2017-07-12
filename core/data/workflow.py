from xml.etree import ElementTree
from copy import deepcopy
from core.executionelement import ExecutionElement
from core import options
from core.step import Step
from core.helpers import extract_workflow_name, UnknownApp, UnknownAppAction

class WorkflowData(ExecutionElement):
    def __init__(self, name='', xml=None, children=None, parent_name='', playbook_name=''):
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=[parent_name])
        self.playbook_name = playbook_name
        self.steps = {}
        if xml is not None:
            self._from_xml(xml)
        else:
            self.start_step = 'start'
        self.children = children if (children is not None) else {}
        self.is_completed = False
        self.accumulated_risk = 0.0
        self.total_risk = float(sum([step.risk for step in self.steps.values() if step.risk > 0]))
        self.is_paused = False
        self.executor = None
        self.breakpoint_steps = []
        self.accumulator = {}
        self.uid = None

    def _from_xml(self, xml_element, *args):
        self.options = options.Options(xml=xml_element.find('.//options'), playbook_name=self.playbook_name)
        start_step = xml_element.find('start')
        self.start_step = start_step.text if start_step is not None else 'start'
        self.steps = {}
        for step_xml in xml_element.findall('.//steps/*'):
            step = Step(xml=step_xml, parent_name=self.name, ancestry=self.ancestry)
            self.steps[step.name] = step

    def to_xml(self, *args):
        """Converts the Workflow object to XML format.

        Returns:
            The XML representation of the Workflow object.
        """
        workflow_element = ElementTree.Element('workflow')
        workflow_element.set('name', extract_workflow_name(self.name))

        workflow_element.append(self.options.to_xml())

        start = ElementTree.SubElement(workflow_element, 'start')
        start.text = self.start_step

        steps = ElementTree.SubElement(workflow_element, 'steps')
        for step_name, step in self.steps.items():
            steps.append(step.to_xml())
        return workflow_element

    def as_json(self, *args):
        """Gets the JSON representation of a Step object.

        Returns:
            The JSON representation of a Step object.
        """
        return {'name': self.name,
                'accumulated_risk': "{0:.2f}".format(self.accumulated_risk * 100.00),
                'options': self.options.as_json(),
                'steps': {name: step.as_json() for name, step in self.steps.items()}}

    def get_cytoscape_data(self):
        """Gets the cytoscape data for the Workflow object.

        Returns:
            The cytoscape data for the Workflow.
        """
        output = []
        for step in self.steps:
            node_id = self.steps[step].name if self.steps[step].name is not None else 'None'
            step_json = self.steps[step].as_json()
            position = step_json.pop('position')
            node = {"group": "nodes", "data": {"id": node_id, "parameters": step_json},
                    "position": {pos: float(val) for pos, val in position.items()}}
            output.append(node)
            for next_step in self.steps[step].conditionals:
                edge_id = str(node_id) + str(next_step.name)
                if next_step.name in self.steps:
                    node = {"group": "edges",
                            "data": {"id": edge_id, "source": node_id, "target": next_step.name,
                                     "parameters": next_step.as_json()}}
                    output.append(node)
        return output

    def from_cytoscape_data(self, data):
        """Reconstruct a Workflow object based on cytoscape data.

        Args:
            data (JSON dict): The cytoscape data to be parsed and reconstructed into a Workflow object.
        """
        backup_steps = deepcopy(self.steps)
        self.steps = {}
        try:
            for node in data:
                if 'source' not in node['data'] and 'target' not in node['data']:
                    step_data = node['data']
                    step_name = step_data['parameters']['name']
                    self.steps[step_name] = Step.from_json(step_data['parameters'],
                                                           node['position'],
                                                           parent_name=self.name,
                                                           ancestry=self.ancestry)
        except (UnknownApp, UnknownAppAction):
            self.steps = backup_steps
            raise

    def reconstruct_ancestry(self, parent_ancestry):
        """Reconstructs the ancestry for a Workflow object. This is needed in case a workflow and/or playbook is renamed.

        Args:
            parent_ancestry(list[str]): The parent ancestry list.
        """
        self._construct_ancestry(parent_ancestry)
        for key in self.steps:
            self.steps[key].reconstruct_ancestry(self.ancestry)

    def get_children(self, ancestry):
        """Gets the children Steps of the Workflow in JSON format.

        Args:
            ancestry (list[str]): The ancestry list for the Step to be returned.

        Returns:
            The Step in the ancestry (if provided) as a JSON, otherwise None.
        """
        if not ancestry:
            return {'steps': list(self.steps.keys())}
        else:
            ancestry = ancestry[::-1]
            next_child = ancestry.pop()
            if next_child in self.steps:
                return self.steps[next_child].get_children(ancestry)
            else:
                return None