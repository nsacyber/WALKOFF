class ExecutionElement(object):
    def __init__(self, name='', parent_name='', ancestry=None):
        self.name = name
        self.parent_name = parent_name
        self._construct_ancestry(ancestry)

    def _construct_ancestry(self, ancestry):
        self.ancestry = list(ancestry) if ancestry is not None else [self.parent_name]
        self.ancestry.append(self.name)

    def _from_xml(self, xml_element, *args):
        raise NotImplementedError('from_xml(xml_element) has not been implemented')

    def to_xml(self, xml_element):
        raise NotImplementedError('to_xml(xml_element) has not been implemented')
