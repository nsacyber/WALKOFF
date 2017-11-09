class JsonElementReader(object):
    """
    Reads an ExecutionElement and converts it to JSON
    """

    @staticmethod
    def read(element):
        """
        Reads an ExecutionElement and converts it to JSON

        Args:
            element (ExecutionElement): The ExecutionElement

        Returns:
            (dict) The JSON representation of the ExecutionElement
        """
        from core.executionelements.executionelement import ExecutionElement
        accumulator = {}
        for field, value in ((field, getattr(element, field)) for field in dir(element)
                             if not field.startswith('_')
                             and not callable(getattr(element, field))
                             and field != 'raw_representation'):
            if isinstance(value, list):
                JsonElementReader._read_list(field, value, accumulator)
            elif isinstance(value, dict):
                JsonElementReader._read_dict(field, value, accumulator)
            elif isinstance(value, bool):
                if value:
                    accumulator[field] = value
            elif isinstance(value, ExecutionElement):
                accumulator[field] = JsonElementReader.read(value)
            elif value is not None:
                accumulator[field] = value
        return accumulator

    @staticmethod
    def _read_list(field_name, list_, accumulator):
        accumulator[field_name] = [JsonElementReader.read(list_value)
                                   if type(list_value) not in (float, str, int, bool) else list_value
                                   for list_value in list_ if list_value is not None]

    @staticmethod
    def _read_dict(field_name, dict_, accumulator):
        from core.executionelements.executionelement import ExecutionElement
        if dict_ and all(isinstance(dict_value, ExecutionElement) for dict_value in dict_.values()):
            accumulator[field_name] = [JsonElementReader.read(dict_value) for dict_value in dict_.values()]
        elif dict_ and all(isinstance(dict_value, list) for dict_value in dict_.values()):
            if all((isinstance(list_value, ExecutionElement) for list_value in dict_value) for dict_value in dict_.values()):
                field_accumulator = []
                for dict_value in dict_.values():
                    list_acc = [JsonElementReader.read(list_value) for list_value in dict_value]
                    field_accumulator.extend(list_acc)
                accumulator[field_name] = field_accumulator
        elif field_name == 'position':
            accumulator[field_name] = dict_
        else:
            accumulator[field_name] = [{'name': dict_key, 'value': dict_value} for dict_key, dict_value in dict_.items()
                                       if not isinstance(dict_value, ExecutionElement)]
