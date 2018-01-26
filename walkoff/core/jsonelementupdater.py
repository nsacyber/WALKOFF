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
        from walkoff.coredb.workflow import Workflow
        from walkoff.coredb.position import Position
        fields_to_update = list(JsonElementUpdater.updatable_fields(element))
        is_workflow = isinstance(element, Workflow)
        if is_workflow:
            JsonElementUpdater.enforce_iteration_order(fields_to_update)
        action_id_map = {}
        for field, value in fields_to_update:
            if field in json_in:
                json_value = json_in[field]
                if isinstance(json_value, list):

                    if is_workflow and field == 'branches':
                        json_value = JsonElementUpdater.update_branch_ids(json_value, action_id_map)

                    cls = getattr(element.__class__, field).property.mapper.class_
                    id_map = JsonElementUpdater.update_relationship(json_value, value, cls)

                    if is_workflow and field == 'actions':
                        action_id_map = id_map
                        for action_json in json_value:
                            if action_json['arguments']:
                                JsonElementUpdater.update_arg_ref_ids(action_json['arguments'], action_id_map)

                elif field == 'position':
                    if 'id' not in json_value:
                        value.position = Position(**json_in)
                    else:
                        value.update(json_value)

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
    def update_arg_ref_ids(arguments_json, action_id_map):
        for argument_json in arguments_json:
            if 'reference' in argument_json:
                if argument_json['reference'] in action_id_map:
                    argument_json['reference'] = action_id_map[argument_json['reference']]

    @staticmethod
    def enforce_iteration_order(fields_to_update):
        items_to_store = {}
        field_order = ['start', 'branches', 'actions']

        for field, value in fields_to_update:
            if field in field_order:
                items_to_store[field] = (field, value)

        for field in field_order:
            fields_to_update.remove(items_to_store[field])
            fields_to_update.insert(0, items_to_store[field])

    @staticmethod
    def update_relationship(json_value, value, cls):
        from walkoff.coredb.argument import Argument
        json_ids = {element['id'] for element in json_value if 'id' in element}

        old_elements = {element.id: element for element in value}
        elements_to_discard = [element for element_id, element in old_elements.items() if
                               element_id not in json_ids]
        id_map = {}
        for json_element in json_value:
            json_element_id = json_element.pop('id', None)
            if json_element_id is not None and json_element_id > 0:
                old_elements[json_element_id].update(json_element)
                id_map[json_element_id] = json_element_id
            else:
                if cls is Argument:
                    new_element = Argument(**json_element)
                else:
                    new_element = cls.create(json_element)
                value.append(new_element)
                if json_element_id is not None:
                    id_map[json_element_id] = new_element.id

        for element in elements_to_discard:
            walkoff.coredb.devicedb.device_db.session.delete(element)
        return id_map

    @staticmethod
    def updatable_fields(element):
        return ((field, getattr(element, field)) for field in dir(element)
                if not field.startswith('_')
                and not callable(getattr(element, field))
                and field != 'raw_representation'
                and field != 'metadata')
