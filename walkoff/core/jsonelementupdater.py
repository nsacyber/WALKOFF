import walkoff.coredb.devicedb
from sqlalchemy.orm import relationship


class JsonElementUpdater(object):
    """Updates an ExecutionElement from JSON
    """

    @staticmethod
    def update(element, json_in):
        """Updates an ExecutionElement from JSON

        Args:
            element (ExecutionElement): The ExecutionElement
        """
        from walkoff.coredb.workflow import Workflow
        fields_to_update = list(JsonElementUpdater.updatable_fields(element))
        is_workflow = isinstance(element, Workflow)
        if is_workflow:
            JsonElementUpdater.enforce_iteration_order(fields_to_update)
        action_id_map = {}
        for field, value in fields_to_update:
            if field in json_in:
                json_value = json_in[field]
                if isinstance(value, relationship):
                    if not isinstance(json_value, list):
                        raise Exception()

                    if is_workflow and field == 'branches':
                        json_value = JsonElementUpdater.update_branch_ids(json_value, action_id_map)

                    id_map = JsonElementUpdater.update_relationship(json_value, value)

                    if is_workflow and field == 'actions':
                        action_id_map = id_map

                else:
                    if is_workflow and field == 'start':
                        json_value = action_id_map[json_value]
                    setattr(element, field, json_value)

    @staticmethod
    def update_branch_ids(json_value, action_id_map):
        for branch_json in json_value:
            if branch_json['source_id'] in action_id_map:
                branch_json['source_id'] = action_id_map[branch_json['source_id']]
            if branch_json['destination_id'] in action_id_map:
                branch_json['destination_id'] = action_id_map[branch_json['destination_id']]
        return json_value

    @staticmethod
    def enforce_iteration_order(fields_to_update):
        field_order = ['actions', 'branches', 'start']
        for field in field_order:
            fields_to_update.remove(field)
        for field in reversed(field_order):
            fields_to_update.append(field)
        fields_to_update.reverse()

    @staticmethod
    def update_relationship(json_value, value):
        json_ids = {element['id'] for element in json_value if 'id' in element}

        old_elements = {element.id: element for element in value}
        elements_to_discard = [element for element_id, element in old_elements.values() if
                               element_id not in json_ids]
        id_map = {}
        for json_element in json_value:
            json_element_id = json_element.pop('id', None)
            if json_element_id is not None:
                json_element.pop('id')
                old_elements['id'].update(json_element)
            else:
                new_element = value.property.mapper.class_.create(json_element)
                value.append(new_element)
                id_map[json_element_id] = new_element.id

        for element in elements_to_discard:
            walkoff.coredb.devicedb.device_db.session.delete(element)
        return id_map

    @staticmethod
    def updatable_fields(element):
        return ((field, getattr(element, field)) for field in dir(element)
                if not field.startswith('_')
                and not callable(getattr(element, field))
                and field != 'raw_representation')
