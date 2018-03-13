from blinker import NamedSignal
from enum import unique, Enum


@unique
class MessageAction(Enum):
    """The types of actions which can be taken on an action
    """
    read = 1
    unread = 2
    delete = 3
    respond = 4

    @classmethod
    def get_all_action_names(cls):
        """Gets a list of all the actions which can be taken on an action as a list of strings

        Returns:
            list[str]: The list of actions which can be taken on an action.
        """
        return [action.name for action in cls]

    @classmethod
    def convert_string(cls, name):
        """Converts a string to an enum

        Args:
            name (str): The name to convert

        Returns:
            MessageAction: The enum representation of this string
        """
        return next((action for action in cls if action.name == name), None)


@unique
class MessageActionEvent(Enum):
    """The types of an events which can be taken on an action.
    """
    created = NamedSignal('message created')
    read = NamedSignal('message read')
    responded = NamedSignal('message responded')

    def send(self, message, **data):
        self.value.send(message, **data)

    def connect(self, func):
        self.value.connect(func)
        return func
