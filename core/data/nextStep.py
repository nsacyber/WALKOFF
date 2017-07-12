from xml.etree import ElementTree
from core.executionelement import ExecutionElement
from core.flag import Flag

class NextStepData(ExecutionElement):
    def __init__(self, xml=None, status='Success', name='', parent_name='', flags=None, ancestry=None):
        if xml is not None:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
        else:
            ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
            self.status = status
            self.flags = flags if flags is not None else []

    def _from_xml(self, xml_element, parent_name='', ancestry=None):
        name = xml_element.get('step')
        status_field = xml_element.find('status')
        self.status = status_field.text if status_field is not None else 'Success'

        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        self.flags = [Flag(xml=flag_element, parent_name=self.name, ancestry=self.ancestry)
                      for flag_element in xml_element.findall('flag')]

    def to_xml(self):
        """Converts the NextStep object to XML format.

        Returns:
            The XML representation of the NextStep object.
        """
        if self.name is not None:
            elem = ElementTree.Element('next')
            name = self.name if self.name else ''
            elem.set('step', name)

            if self.status.lower() != 'success':
                status = ElementTree.Element('status')
                status.text = self.status
                elem.append(status)

            if self.flags:
                for flag in self.flags:
                    elem.append(flag.to_xml())
            return elem

    def as_json(self, with_children=True):
        """Gets the JSON representation of a NextStep object.

        Args:
            with_children (bool, optional): A boolean to determine whether or not the children elements of the NextStep
                object should be included in the output.

        Returns:
            The JSON representation of a NextStep object.
        """
        name = str(self.name) if self.name else ''
        if with_children:
            return {"flags": [flag.as_json() for flag in self.flags],
                    "status": self.status,
                    "name": name}
        else:
            return {"flags": [flag.name for flag in self.flags],
                    "status": self.status,
                    "name": name}

    @staticmethod
    def from_json(json, parent_name='', ancestry=None):
        """Forms a NextStep object from the provided JSON object.

        Args:
            json (JSON object): The JSON object to convert from.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            ancestry (list[str], optional): The ancestry for the new NextStep object. Defaults to None.

        Returns:
            The NextStep object parsed from the JSON object.
        """
        name = json['name'] if 'name' in json else ''
        status = json['status'] if 'status' in json else 'Success'
        next_step = NextStepData(name=name, status=status, parent_name=parent_name, ancestry=ancestry)
        if json['flags']:
            next_step.flags = [Flag.from_json(flag, parent_name=next_step.parent_name, ancestry=next_step.ancestry)
                               for flag in json['flags']]
        return next_step