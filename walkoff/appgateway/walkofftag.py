from enum import unique, Enum


@unique
class WalkoffTag(Enum):
    """The tags used to determine if a function in an app is an Action, Condition, or Transform.
    """
    action = 'action'
    condition = 'condition'
    transform = 'transform'

    def tag(self, func):
        """Tags a function with the enum

        Args:
            func (func): The function to tag
        """
        setattr(func, self.value, True)

    def is_tagged(self, func):
        """Determines if a function is tagged with the enum

        Args:
            func (func): The function to inspect

        Returns:
            (bool): Is the function tagged with the enum?
        """
        return getattr(func, self.value, False)

    @classmethod
    def get_tags(cls, func):
        """Gets all the tags associated with the function

        Args:
            func (func): The function to inspect

        Returns:
            set(WalkoffTag): All the tags associated with this function
        """
        return {tag for tag in cls if getattr(func, tag.value, False)}
