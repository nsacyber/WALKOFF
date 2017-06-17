from xml.etree import ElementTree
import logging
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.flag import Flag

logger = logging.getLogger(__name__)


class NextStep(ExecutionElement):
    def __init__(self, xml=None, name='', parent_name='', flags=None, ancestry=None):
        """Initializes a new NextStep object.
        
        Args:
            xml (cElementTree, optional): The XML element tree object. Defaults to None.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            name (str, optional): The name of the NextStep object. Defaults to an empty string.
            flags (list[Flag], optional): A list of Flag objects for the NextStep object. Defaults to None.
            ancestry (list[str], optional): The ancestry for the NextStep object. Defaults to None.
        """
        if xml is not None:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
        else:
            ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
            self.flags = flags if flags is not None else []

    def _from_xml(self, xml_element, parent_name='', ancestry=None):
        name = xml_element.get('step')
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        self.flags = [Flag(xml=flag_element, parent_name=self.name, ancestry=self.ancestry)
                      for flag_element in xml_element.findall('flag')]

    def reconstruct_ancestry(self, parent_ancestry):
        """Reconstructs the ancestry for a NextStep object. This is needed in case a workflow and/or playbook is renamed.
        
        Args:
            parent_ancestry(list[str]): The parent ancestry list.
        """
        self._construct_ancestry(parent_ancestry)
        for flag in self.flags:
            flag.reconstruct_ancestry(self.ancestry)

    def to_xml(self, tag='next'):
        """Converts the NextStep object to XML format.
        
        Args:
            tag (str, optional): The tag name for the NextStep object. Defaults to "next".
            
        Returns:
            The XML representation of the NextStep object.
        """
        if self.name is not None:
            elem = ElementTree.Element(tag)
            name = self.name if self.name else ''
            elem.set('step', name)
            if self.flags:
                for flag in self.flags:
                    elem.append(flag.to_xml())
            return elem

    def __eq__(self, other):
        return self.name == other.name and set(self.flags) == set(other.flags)

    def __call__(self, data_in, accumulator):
        if all(flag(data_in=data_in, accumulator=accumulator) for flag in self.flags):
            callbacks.NextStepTaken.send(self)
            logger.debug('NextStep is valid for input {0}'.format(data_in))
            return self.name
        else:
            logger.debug('NextStep is not valid for input {0}'.format(data_in))
            callbacks.NextStepNotTaken.send(self)
            return None

    def __repr__(self):
        output = {'flags': [flag.as_json() for flag in self.flags],
                  'name': self.name}
        return str(output)

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
                    "name": name}
        else:
            return {"flags": [flag.name for flag in self.flags],
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
        next_step = NextStep(name=name, parent_name=parent_name, ancestry=ancestry)
        if json['flags']:
            next_step.flags = [Flag.from_json(flag, parent_name=next_step.parent_name, ancestry=next_step.ancestry)
                               for flag in json['flags']]
        return next_step

    def get_children(self, ancestry):
        """Gets the children Flags of the NextStep in JSON format.
        
        Args:
            ancestry (list[str]): The ancestry list for the Flag to be returned.
            
        Returns:
            The Flag in the ancestry (if provided) as a JSON, otherwise None.
        """
        if not ancestry:
            return self.as_json(with_children=False)
        else:
            next_child = ancestry.pop()
            try:
                flag_index = [flag.name for flag in self.flags].index(next_child)
                return self.flags[flag_index].get_children(ancestry)
            except ValueError:
                return None
