from collections import OrderedDict
from future.utils import iteritems
import logging

logging.basicConfig()


class JsonElementCreator(object):
    playbook_class_ordering = None

    @classmethod
    def create(cls, json_in, element_class=None):
        from core.executionelements.playbook import Playbook
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
            if subfield_lookup is not None:
                for subfield_name, next_class in subfield_lookup.items():
                    if subfield_name in json_in:
                        subfield_json = json_in[subfield_name]
                        if hasattr(current_class, '_templatable'):
                            json_in['raw_representation'] = dict(json_in)
                        json_in[subfield_name] = [next_class.create(element_json) for element_json in subfield_json]
            return current_class(**json_in)
        except (KeyError, TypeError) as e:
            from core.helpers import format_exception_message
            raise ValueError('Improperly formatted JSON for ExecutionElement object {}'.format(format_exception_message(e)))

    @classmethod
    def _setup_ordering(cls):
        if cls.playbook_class_ordering is None:
            from core.executionelements.playbook import Playbook
            from core.executionelements.workflow import Workflow
            from core.executionelements.step import Step
            from core.executionelements.nextstep import NextStep
            from core.executionelements.flag import Flag
            from core.executionelements.filter import Filter
            cls.playbook_class_ordering = OrderedDict([
                (Playbook, {'workflows': Workflow}),
                (Workflow, {'steps': Step}),
                (Step, {'next_steps': NextStep, 'triggers': Flag}),
                (NextStep, {'flags': Flag}),
                (Flag, {'filters': Filter}),
                (Filter, None)
            ])
