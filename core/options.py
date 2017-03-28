from core.executionelement import ExecutionElement
import xml.etree.cElementTree as elementtree
from core.helpers import construct_workflow_name_key

class Options(ExecutionElement):
    def __init__(self, xml=None, scheduler=None, children=None, enabled=False, workflow_name='', options_name='', filename=''):
        if xml is not None:
            self._from_xml(xml, filename=filename)
        else:
            ExecutionElement.__init__(self, name=options_name, parent_name=workflow_name)
            self.scheduler = scheduler if scheduler is not None else {}
            self.enabled = enabled
            self.children = children if children is not None else {}

    def _from_xml(self, xml_element, options_name='Default', workflow_name='', filename=''):
        ExecutionElement.__init__(self, name=options_name, parent_name=workflow_name)
        self.scheduler = {'autorun': xml_element.find('.//scheduler').get('autorun'),
                          'type': xml_element.find('.//scheduler').get('type'),
                          'args': {option.tag: option.text for option in xml_element.findall('.//scheduler/*')}}
        self.enabled = bool(xml_element.find('.//enabled').text)
        self.children = {construct_workflow_name_key(filename, child.text): None for child in xml_element.findall('.//children/child')}

    def to_xml(self, *args):
        options = elementtree.Element('options')

        enabled = elementtree.SubElement(options, 'enabled')
        enabled.text = str(self.enabled).lower()

        scheduler = elementtree.SubElement(options, 'scheduler')
        scheduler.set('type', self.scheduler['type'])
        scheduler.set('autorun', self.scheduler['autorun'])

        for arg, value in self.scheduler['args'].items():
            name = elementtree.SubElement(scheduler, arg)
            name.text = value

        return options

    def as_json(self):
        return {'scheduler': self.scheduler,
                'enabled': str(self.enabled),
                'children': self.children}

    def __repr__(self):
        result = {'scheduler': str(self.scheduler),
                  'enabled': str(self.enabled),
                  'children': str(self.children)}
        return str(result)
