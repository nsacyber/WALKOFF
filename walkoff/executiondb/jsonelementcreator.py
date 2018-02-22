from collections import OrderedDict

from six import iteritems
import walkoff.executiondb.devicedb
from walkoff.helpers import UnknownFunction, UnknownApp, InvalidArgument


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
        from walkoff.executiondb.playbook import Playbook
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
            walkoff.executiondb.devicedb.device_db.session.add(elem)
            return elem
        except (KeyError, TypeError, InvalidArgument, UnknownApp, UnknownFunction) as e:
            import traceback
            traceback.print_exc()
            walkoff.executiondb.devicedb.device_db.session.rollback()
            from walkoff.helpers import format_exception_message
            raise ValueError(
                'Improperly formatted JSON for ExecutionElement {0} {1}'.format(current_class.__name__,
                                                                                format_exception_message(e)))

    @classmethod
    def construct_current_class(cls, current_class, json_in, subfield_lookup):
        from walkoff.executiondb.argument import Argument
        from walkoff.executiondb.position import Position
        from walkoff.executiondb.conditionalexpression import ConditionalExpression
        if subfield_lookup is not None:
            for subfield_name, next_class in subfield_lookup.items():
                if subfield_name in json_in:
                    subfield_json = json_in[subfield_name]
                    if next_class is ConditionalExpression and current_class is not ConditionalExpression:
                        json_in[subfield_name] = next_class.create(subfield_json)
                    else:
                        json_in[subfield_name] = [next_class.create(element_json) for element_json in subfield_json]

        if 'arguments' in json_in:
            for arg_json in json_in['arguments']:
                arg_json.pop('id', None)
            json_in['arguments'] = [Argument(**arg_json) for arg_json in json_in['arguments']]
        if 'position' in json_in:
            json_in['position'].pop('id', None)
            json_in['position'] = Position(**json_in['position'])
        return current_class(**json_in)

    @classmethod
    def _setup_ordering(cls):
        if cls.playbook_class_ordering is None:
            from walkoff.executiondb.playbook import Playbook
            from walkoff.executiondb.workflow import Workflow
            from walkoff.executiondb.action import Action
            from walkoff.executiondb.branch import Branch
            from walkoff.executiondb.conditionalexpression import ConditionalExpression
            from walkoff.executiondb.condition import Condition
            from walkoff.executiondb.transform import Transform
            cls.playbook_class_ordering = OrderedDict([
                (Playbook, {'workflows': Workflow}),
                (Workflow, OrderedDict([('actions', Action), ('branches', Branch)])),
                (Action, {'trigger': ConditionalExpression}),
                (Branch, {'condition': ConditionalExpression}),
                (ConditionalExpression, {'conditions': Condition, 'child_expressions': ConditionalExpression}),
                (Condition, {'transforms': Transform}),
                (Transform, None)
            ])

