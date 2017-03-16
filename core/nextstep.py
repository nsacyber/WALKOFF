import xml.etree.cElementTree as et

from core.case import callbacks
from core.executionelement import ExecutionElement
from core.flag import Flag


class Next(ExecutionElement):
    def __init__(self, xml=None, parent_name='', name='', nextWorkflow='', flags=None, ancestry=None):
        if xml is not None:
            self._from_xml(xml, parent_name=parent_name, ancestry=ancestry)
        else:
            ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
            self.flags = flags if flags is not None else []
        super(Next, self)._register_event_callbacks({'NextStepTaken': callbacks.add_next_step_entry('Step taken'),
                                                     'NextStepNotTaken': callbacks.add_next_step_entry('Step not taken')})

    def _from_xml(self, xml_element, parent_name='', ancestry=None):
        name = xml_element.get('step')
        ExecutionElement.__init__(self, name=name, parent_name=parent_name, ancestry=ancestry)
        self.flags = [Flag(xml=flag_element, parent_name=self.name, ancestry=self.ancestry)
                      for flag_element in xml_element.findall('flag')]

    def to_xml(self, tag='next'):
        if self.name is not None:
            elem = et.Element(tag)
            elem.set('next', self.name)
            for flag in self.flags:
                elem.append(flag.to_xml())
            return elem

    def createFlag(self, action="", args=None, filters=None):
        new_flag = Flag(action=action,
                       args=(args if args is not None else {}),
                       filters=(filters if filters is not None else []))
        self.flags.append(new_flag)

    def removeFlag(self, index=-1):
        try:
            self.flags.remove(self.flags[index])

            # Reflect change in XML
            # selected = self.xml.find(".//flag[" + str(index) + "]")
            # self.xml.find(".").remove(selected)
            return True
        except IndexError:
            return False

    def __eq__(self, other):
        return self.name == other.name and set(self.flags) == set(other.flags)

    def __call__(self, output=None):
        if all(flag(output=output) for flag in self.flags):
            self.event_handler.execute_event_code(self, 'NextStepTaken')
            return self.name
        else:
            self.event_handler.execute_event_code(self, 'NextStepNotTaken')
            return None

    def __repr__(self):
        output = {'nextStep': self.name,
                  'flags': [flag.__dict__ for flag in self.flags],
                  'name': self.name}
        return str(output)

    def as_json(self):
        return {"nextStep": str(self.name),
                "flags": [flag.as_json() for flag in self.flags],
                "name": str(self.name)}

    @staticmethod
    def from_json(json, parent_name='', ancestry=None):
        next_step = Next(name=json['name'], parent_name=parent_name, ancestry=ancestry)
        next_step.flags = [Flag.from_json(flag, parent_name=next_step.parent_name, ancestry=next_step.ancestry)
                           for flag in json['flags']]
        return next_step

