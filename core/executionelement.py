class ExecutionElement(object):
    def __init__(self, name='', parent_name='', ancestry=None):
        """Initializes a new ExecutionElement object. This is the parent class.
        Args:
            name (str, optional): The name of the ExecutionElement. Defaults to an empty string.
            parent_name (str, optional): The name of the parent of the ExecutionElement. Defaults to an empty string.
            ancestry (str, optional): The ancestry for the ExecutionElement. Defaults to None.
        """
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

    def as_json(self, *args):
        raise NotImplementedError('as_json has not been implemented')

    def get_children(self, ancestry):
        raise NotImplementedError('get_children has not been implemented')
