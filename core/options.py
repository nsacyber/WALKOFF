from core.executionelement import ExecutionElement


class Options(ExecutionElement):
    def __init__(self, xml=None, scheduler=None, children=None, enabled=False, workflow_name='', options_name=''):
        if xml is not None:
            self._from_xml(xml)
        else:
            ExecutionElement.__init__(self, name=options_name, parent_name=workflow_name)
            self.scheduler = scheduler if scheduler is not None else {}
            self.enabled = enabled
            self.children = children if children is not None else {}

    def _from_xml(self, xml_element, options_name='Default', workflow_name=''):
        ExecutionElement.__init__(self, name=options_name, parent_name=workflow_name)
        self.scheduler = {"autorun": xml_element.find(".//scheduler").get("autorun"),
                          "type": xml_element.find(".//scheduler").get("type"),
                          "args": {option.tag: option.text for option in xml_element.findall(".//scheduler/*")}}
        self.enabled = xml_element.find(".//enabled").text
        self.children = {child.text: None for child in xml_element.findall(".//children/child")}

    def __repr__(self):
        result = {'scheduler': str(self.scheduler),
                  'enabled': str(self.enabled),
                  'children': str(self.children)}
        return str(result)
