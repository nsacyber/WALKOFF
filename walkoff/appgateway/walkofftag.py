from enum import unique, Enum


@unique
class WalkoffTag(Enum):
    action = 'action'
    condition = 'condition'
    transform = 'transform'

    def tag(self, func):
        setattr(func, self.value, True)

    def is_tagged(self, func):
        return getattr(func, self.value, False)

    @classmethod
    def get_tags(cls, func):
        return {tag for tag in cls if getattr(func, tag.value, False)}
