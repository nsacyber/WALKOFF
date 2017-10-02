class JsonElementCreator(object):
    playbook_class_ordering = None

    @classmethod
    def create(cls, json_in, element_class=None):
        from core.playbook import Playbook
        cls._setup_ordering()
        if element_class is None:
            element_class = Playbook
        class_iterator = iter(cls.playbook_class_ordering)
        current_class, current_subfield_name = next(class_iterator)
        while current_class != element_class:
            try:
                current_class, current_subfield_name = next(class_iterator)
            except StopIteration:
                raise ValueError('Unknown class {}'.format(element_class.__class__.__name__))
        try:
            if current_subfield_name is not None:
                next_class, _ = next(class_iterator)
                subfield_json = json_in[current_subfield_name]
                json_in[current_subfield_name] = [next_class.create(element_json) for element_json in subfield_json]

            return current_class(**json_in)
        except (KeyError, TypeError):
            raise ValueError('Improperly formatted JSON for ExecutionElement object')

    @classmethod
    def _setup_ordering(cls):
        if cls.playbook_class_ordering is None:
            from core.playbook import Playbook
            from core.workflow import Workflow
            from core.step import Step
            from core.nextstep import NextStep
            from core.flag import Flag
            from core.filter import Filter
            cls.playbook_class_ordering = (
                (Playbook, 'workflows'), (Workflow, 'steps'), (Step, 'next'), (NextStep, 'flags'),
                (Flag, 'filters'), (Filter, None))
