from core.events import EventHandler

class ExecutionElement(object):
    def __init__(self, name='', parent_name='', ancestry=None):
        self.name = name
        self.parent_name = parent_name
        self.ancestry = list(ancestry) if ancestry is not None else [parent_name]
        self.ancestry.append(self.name)
        self.event_handler = EventHandler(self.__class__.__name__ + 'EventHandler')

    def _construct_ancestry(self, ancestry):
        self.ancestry = list(ancestry) if ancestry is not None else [parent_name]
        self.ancestry.append(self.name)

    def _register_event_callbacks(self, callbacks):
        self.event_handler.add_events(callbacks)

    def _from_xml(self, xml_element, *args):
        raise NotImplementedError('from_xml(xml_element) has not been implemented')

    def to_xml(self, xml_element):
        raise NotImplementedError('to_xml(xml_element) has not been implemented')