from xml.etree import cElementTree


class Options(object):
    def __init__(self, xml=None, scheduler=None, children=None, enabled=False):
        """Initializes a new Options object.
        
        Args:
            xml (cElementTree, optional): The XML element tree object. Defaults to None.
            scheduler (dict, optional): The scheduler dictionary, which has "autorun", "type", and "args" fields. 
                Defaults to None.
            children (dict, optional): Dict of children options. Defaults to None.
            enabled (bool, optional): Boolean to determine whether or not the options are enabled or disabled. Defaults
                to False.
        """
        if xml is not None:
            self._from_xml(xml)
        else:
            self.scheduler = scheduler if scheduler is not None else {}
            self.enabled = enabled
            self.children = children if children is not None else {}

    def _from_xml(self, xml_element):
        self.scheduler = {"autorun": xml_element.find('.//scheduler').get('autorun'),
                          "type": xml_element.find('.//scheduler').get('type'),
                          "args": {option.tag: option.text for option in xml_element.findall('.//scheduler/*')}}
        self.enabled = bool(xml_element.find('.//enabled').text)
        self.children = {child.text: None
                         for child in xml_element.findall('.//children/child')}

    def to_xml(self):
        """Converts the Options object to XML format.
        
        Returns:
            The XML representation of the Options object.
        """
        options = cElementTree.Element('options')

        enabled = cElementTree.SubElement(options, 'enabled')
        enabled.text = str(self.enabled).lower()

        scheduler = cElementTree.SubElement(options, 'scheduler')
        scheduler.set('type', self.scheduler['type'])
        scheduler.set('autorun', self.scheduler['autorun'])

        for arg, value in self.scheduler['args'].items():
            name = cElementTree.SubElement(scheduler, arg)
            name.text = value

        return options

    def as_json(self):
        """Gets the JSON representation of an Options object.
        
        Returns:
            The JSON representation of an Options object.
        """
        return {"scheduler": self.scheduler,
                "enabled": self.enabled,
                "children": [child.name for child in self.children.values()]}

    @staticmethod
    def from_json(json_in):
        return Options(scheduler=json_in['scheduler'],
                       enabled=json_in['enabled'],
                       children={name: None for name in json_in['children']})

    def __repr__(self):
        return str({'scheduler': self.scheduler,
                    'enabled': self.enabled,
                    'children': self.children})
