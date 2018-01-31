import walkoff.coredb.devicedb


class JsonElementUpdater(object):
    """Updates an ExecutionElement from JSON
    """

    @staticmethod
    def update(element, json_in):
        """Updates an ExecutionElement from JSON

        Args:
            element (ExecutionElement): The ExecutionElement
        """
        from walkoff.coredb.position import Position
        fields_to_update = list(JsonElementUpdater.updatable_fields(element))
        for field, value in fields_to_update:
            if field in json_in:
                json_value = json_in[field]
                if isinstance(json_value, list) and field != 'selection':

                    cls = getattr(element.__class__, field).property.mapper.class_
                    JsonElementUpdater.update_relationship(json_value, value, cls)

                elif field == 'position':
                    if 'id' not in json_value:
                        value.position = Position(**json_in)
                    else:
                        value.update(json_value)

                else:
                    setattr(element, field, json_value)
            elif field != 'id':
                if isinstance(value, list):
                    setattr(element, field, [])
                else:
                    setattr(element, field, None)

    @staticmethod
    def update_relationship(json_value, value, cls):
        from walkoff.coredb.argument import Argument
        json_ids = {element['id'] for element in json_value if 'id' in element}

        old_elements = {element.id: element for element in value}
        elements_to_discard = [element for element_id, element in old_elements.items() if
                               element_id not in json_ids]
        for json_element in json_value:
            json_element_id = json_element.pop('id', None)
            if json_element_id is not None and json_element_id > 0:
                old_elements[json_element_id].update(json_element)
            else:
                if cls is Argument:
                    new_element = Argument(**json_element)
                else:
                    new_element = cls.create(json_element)
                value.append(new_element)

        for element in elements_to_discard:
            walkoff.coredb.devicedb.device_db.session.delete(element)

    @staticmethod
    def updatable_fields(element):
        return ((field, getattr(element, field)) for field in dir(element)
                if not field.startswith('_')
                and not callable(getattr(element, field))
                and field != 'raw_representation'
                and field != 'metadata')
