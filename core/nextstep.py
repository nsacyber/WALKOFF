from xml.etree import ElementTree
import logging
from core.case import callbacks
from core.executionelement import ExecutionElement
from core.flag import Flag
import uuid

logger = logging.getLogger(__name__)


class NextStep(ExecutionElement):
    def __init__(self, xml=None, status='Success', name='', parent_name='', flags=None, ancestry=None, uid=None):
        """Initializes a new NextStep object.
        
        Args:
            xml (cElementTree, optional): The XML element tree object. Defaults to None.
            parent_name (str, optional): The name of the parent for ancestry purposes. Defaults to an empty string.
            name (str, optional): The name of the NextStep object. Defaults to an empty string.
            flags (list[Flag], optional): A list of Flag objects for the NextStep object. Defaults to None.
            ancestry (list[str], optional): The ancestry for the NextStep object. Defaults to None.
            uid (str, optional): A universally unique identifier for this object. Created from uuid.uuid4().hex in Python
        """
        if xml is not None:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
            self.uid = uuid.uuid4().hex
        else:
            ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
            self.status = status
            self.flags = flags if flags is not None else []
            self.uid = uuid.uuid4().hex if uid is None else uid

    def _from_xml(self, xml_element, parent_name='', ancestry=None):
        name = xml_element.get('step')
        status_field = xml_element.find('status')
        self.status = status_field.text if status_field is not None else 'Success'

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

    def __eq__(self, other):
        return self.name == other.name and self.status == other.status and set(self.flags) == set(other.flags)

    def __call__(self, data_in, accumulator):
        if data_in is not None and data_in.status == self.status:
            if all(flag(data_in=data_in.result, accumulator=accumulator) for flag in self.flags):
                callbacks.NextStepTaken.send(self)
                logger.debug('NextStep is valid for input {0}'.format(data_in))
                return self.name
            else:
                logger.debug('NextStep is not valid for input {0}'.format(data_in))
                callbacks.NextStepNotTaken.send(self)
                return None
        else:
            return None

    def __repr__(self):
        output = {'uid': self.uid,
                  'flags': [flag.as_json() for flag in self.flags],
                  'status': self.status,
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
            return {"uid": self.uid,
                    "flags": [flag.as_json() for flag in self.flags],
                    "status": self.status,
                    "name": name}
        else:
            return {"uid": self.uid,
                    "flags": [flag.name for flag in self.flags],
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
        uid = json['uid'] if 'uid' in json else uuid.uuid4().hex
        next_step = NextStep(name=name, status=status, parent_name=parent_name, ancestry=ancestry, uid=uid)
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
