
class Validatable(object):
    children = []

    @property
    def _is_valid(self):
        if self.errors is not None:
            return False
        for child in self.children:
            child = getattr(self, child, None)
            if isinstance(child, list):
                for instance in (instance for instance in child if instance is not None):
                    if not instance._is_valid:
                        return False
            elif child is not None:
                if not child._is_valid:
                    return False
        return True

    def validate(self):
        raise NotImplementedError('Must implement validate_self')
