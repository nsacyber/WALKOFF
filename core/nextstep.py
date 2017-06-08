from xml.etree import cElementTree
import logging
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.flag import Flag

logger = logging.getLogger(__name__)


class NextStep(ExecutionElement):
    def __init__(self, xml=None, parent_name='', name='', flags=None, ancestry=None):
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

    def reconstruct_ancestry(self, parent_ancestry):
        """Reconstructs the ancestry for a NextStep object. This is needed in case a workflow and/or playbook is renamed.
        
        Args:
            parent_ancestry(list[str]): The parent ancestry list.
        """
        self._construct_ancestry(parent_ancestry)
        for flag in self.flags:
            flag.reconstruct_ancestry(self.ancestry)

    def _from_xml(self, xml_element, parent_name='', ancestry=None):
        name = xml_element.get('step')
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        self.flags = [Flag(xml=flag_element, parent_name=self.name, ancestry=self.ancestry)
                      for flag_element in xml_element.findall('flag')]

    def to_xml(self, tag='next'):
        """Converts the NextStep object to XML format.
        
        Args:
            tag (str, optional): The tag name for the NextStep object. Defaults to "next".
            
        Returns:
            The XML representation of the NextStep object.
        """
        if self.name is not None:
            elem = cElementTree.Element(tag)
            name = self.name if self.name else ''
            elem.set('step', name)
            for flag in self.flags:
                elem.append(flag.to_xml())
            return elem

    def create_flag(self, action="", args=None, filters=None):
        """Creates a new Flag object and adds it to the NextStep object's list of Flags.
        
        Args:
            action (str, optional): The action name for the Flag. Defaults to an empty string.
            args (dict[str:str], optional): Dictionary of Argument keys to Argument values. This dictionary will be
            converted to a dictionary of str:Argument. Defaults to None.
            filters(list[Filter], optional): A list of Filter objects for the Flag object. Defaults to None.
        """
        new_flag = Flag(action=action,
                        args=(args if args is not None else {}),
                        filters=(filters if filters is not None else []),
                        parent_name=self.name,
                        ancestry=self.ancestry)
        self.flags.append(new_flag)

    def remove_flag(self, index=-1):
        """Removes a Flag object from the NextStep's list of Flags at a given index.
        
        Args:
            index(int): The index of the Flag object to be removed.
            
        Returns:
            True on success, False otherwise.
        """
        try:
            self.flags.remove(self.flags[index])
            logger.debug('Flag {0} removed from next step {1}'.format(index, self.ancestry))
            return True
        except IndexError:
            logger.error('Cannot remove flag {0} from NextStep {1}. Index out of bounds'.format(index, self.ancestry))
            return False

    def __eq__(self, other):
        return self.name == other.name and set(self.flags) == set(other.flags)

    def __call__(self, data_in=None):
        if all(flag(data_in=data_in) for flag in self.flags):
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
