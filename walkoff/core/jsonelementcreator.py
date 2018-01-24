from collections import OrderedDict

from six import iteritems
import walkoff.coredb.devicedb


class JsonElementCreator(object):
    """
    Creates an ExecutionElement from JSON
    """
    playbook_class_ordering = None

    @classmethod
    def create(cls, json_in, element_class=None):
        """
        Creates an ExecutionElement from json

        Args:
            json_in (dict): The JSON to convert to an ExecutionElement
            element_class (cls): The class of the ExecutionElement to convert

        Returns:
            (ExecutionElement) The constructed ExecutionElement
        """
        from walkoff.coredb.playbook import Playbook
        cls._setup_ordering()
        if element_class is None:
            element_class = Playbook
        class_iterator = iteritems(cls.playbook_class_ordering)
        current_class, subfield_lookup = next(class_iterator)
        while current_class != element_class:
            try:
                current_class, subfield_lookup = next(class_iterator)
            except StopIteration:
                raise ValueError('Unknown class {}'.format(element_class.__class__.__name__))
        try:
            elem = cls.construct_current_class(current_class, json_in, subfield_lookup)
            walkoff.coredb.devicedb.device_db.session.add(elem)
            walkoff.coredb.devicedb.device_db.session.flush()
            return elem
        except (KeyError, TypeError) as e:
            from walkoff.helpers import format_exception_message
            raise ValueError(
                'Improperly formatted JSON for ExecutionElement {0} {1}'.format(current_class.__name__,
                                                                                format_exception_message(e)))

    @classmethod
    def construct_current_class(cls, current_class, json_in, subfield_lookup):
        from walkoff.coredb.argument import Argument
        from walkoff.coredb.action import Action
        if subfield_lookup is not None:
            for subfield_name, next_class in subfield_lookup.items():
                if subfield_name in json_in:
                    subfield_json = json_in[subfield_name]
                    if hasattr(current_class, '_templatable'):
                        json_in['raw_representation'] = dict(json_in)

                    if isinstance(next_class, Action):
                        element_lookup = {}
                        json_in[subfield_name] = []
                        for element_json in subfield_json:
                            prev_id = subfield_json.pop('id')
                            element = next_class.create(element_json)
                            json_in[subfield_name].append(element)
                            element_lookup[prev_id] = element.id
                    else:
                        json_in[subfield_name] = [next_class.create(element_json) for element_json in subfield_json]
        if 'arguments' in json_in:
            json_in['arguments'] = [Argument(**arg_json) for arg_json in json_in['arguments']]
        return current_class(**json_in)

    @classmethod
    def _setup_ordering(cls):
        if cls.playbook_class_ordering is None:
            from walkoff.coredb.playbook import Playbook
            from walkoff.coredb.workflow import Workflow
            from walkoff.coredb.action import Action
            from walkoff.coredb.branch import Branch
            from walkoff.coredb.condition import Condition
            from walkoff.coredb.transform import Transform
            cls.playbook_class_ordering = OrderedDict([
                (Playbook, {'workflows': Workflow}),
                (Workflow, OrderedDict([('actions', Action), ('branches', Branch)])),
                (Action, {'triggers': Condition}),
                (Branch, {'conditions': Condition}),
                (Condition, {'transforms': Transform}),
                (Transform, None)
            ])
