import walkoff.coredb.devicedb
from uuid import UUID


class JsonElementUpdater(object):
    """Updates an ExecutionElement from JSON
    """

    @staticmethod
    def update(element, json_in):
        """Updates an ExecutionElement from JSON

        Args:
            element (ExecutionElement): The ExecutionElement
            json_in (dict): The JSON in to update
        """
        from walkoff.coredb.position import Position
        fields_to_update = list(JsonElementUpdater.updatable_fields(element))
        for field_name, field_value in fields_to_update:
            if field_name in json_in:
                json_field_value = json_in[field_name]
                if isinstance(json_field_value, list) and field_name != 'selection':

                    cls = getattr(element.__class__, field_name).property.mapper.class_
                    JsonElementUpdater.update_relationship(json_field_value, field_value, cls)

                elif field_name == 'position':
                    if 'id' not in json_field_value:
                        field_value.position = Position(**json_in)
                    else:
                        field_value.update(json_field_value)

                else:
                    setattr(element, field_name, json_field_value)
            elif field_name != 'id':
                if isinstance(field_value, list):
                    setattr(element, field_name, [])
                else:
                    setattr(element, field_name, None)

    @staticmethod
    def update_relationship(json_field_value, field_value, cls):
        from walkoff.coredb.argument import Argument
        if cls is not Argument:
            json_ids = {UUID(element['id']) for element in json_field_value if 'id' in element}
        else:
            json_ids = {element['id'] for element in json_field_value if 'id' in element}
        if isinstance(field_value, dict):
            old_elements = field_value
        else:
            old_elements = {element.id: element for element in field_value}
        elements_to_discard = [element for element_id, element in old_elements.items() if
                               element_id not in json_ids]
        for json_element in json_field_value:
            json_element_id = json_element.get('id', None)
            json_element_id = UUID(json_element_id) if isinstance(json_element_id, (str, unicode)) else json_element_id
            if json_element_id is not None and json_element_id in old_elements:
                # if cls is not Argument:
                #     json_element_id = UUID(json_element_id)
                old_elements[json_element_id].update(json_element)
            else:
                if cls is Argument:
                    new_element = Argument(**json_element)
                else:
                    new_element = cls.create(json_element)
                field_value.append(new_element)

        for element in elements_to_discard:
            walkoff.coredb.devicedb.device_db.session.delete(element)

    @staticmethod
    def updatable_fields(element):
        return ((field, getattr(element, field)) for field in dir(element)
                if not field.startswith('_')
                and not callable(getattr(element, field))
                and field != 'metadata')
