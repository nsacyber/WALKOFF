import logging
import re

from six import add_metaclass

from walkoff.events import WalkoffEvent

__all__ = ['Text', 'Url', 'AcceptDecline', 'Message', 'send_message']

logger = logging.getLogger(__name__)


def convert_class_name_to_tag(name):
    """
    Converts an upper camelcase Python class name to lower snake case. Used for converting a MessageComponent class name
    to a tag to be used in the JSON

    Args:
        name (str): Name of the class

    Returns:
        (str): The class's tag name
    """
    sub = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', sub).lower()


class MessageComponentTypeRegistry(type):
    """
    Metaclass used for registering subclasses of MessageComponents
    """

    def __init__(cls, name, bases, dct):
        """Constructor for MessageComponentTypeRegistry class

        Args:
            name (str): Name of the class
            bases (Tuple[type]): Bases of the class
            dct (dict(str, any)): Namespace of the class
        """
        if not hasattr(cls, 'registry'):
            cls.registry = {}
            cls.message_type = '__base'
        else:
            cls.message_type = convert_class_name_to_tag(name)
            if cls.message_type not in cls.registry:
                cls.registry[cls.message_type] = cls
            elif cls.registry[cls.message_type] is not cls:
                logger.warning('Class {} is already registered as a message type. Skipping'.format(cls.__name__))
        super(MessageComponentTypeRegistry, cls).__init__(name, bases, dct)


@add_metaclass(MessageComponentTypeRegistry)
class MessageComponent(object):
    """
    Base class for all elements of the body of a message

    Args:
        requires_response(bool, optional): Does this message component necessitate a response from a user?
            Defaults to False
    """

    def __init__(self, requires_response=False):
        self.requires_response = requires_response

    def as_json(self):
        """
        Retrieves the JSON representation of this component. This uses get_component_response and the auto-generated
        message_type to generate JSON of the correct form. This function is not intended to be overridden.

        Returns:
            (dict): The JSON representation of this component
        """
        return {'type': self.message_type, 'requires_response': self.requires_response,
                'data': self.get_component_json()}

    def get_component_json(self):
        """
        Intended to be overridden by subclasses, and should return a normal JSON representation of the object.

        Returns:
            (dict): The JSON representation of the component.
        """
        return {}

    @staticmethod
    def from_json(json_in):
        """
        Constructs a MessageComponent from the JSON returned by the as_json function. This method is not intended to be
        overridden.
        Args:
            json_in (dict): The JSON representation of the object

        Returns:
            (MessageComponent): The constructed message component
        """
        message_component_class = MessageComponent.registry.get(json_in['type'], MessageComponent)
        return message_component_class.from_component_json(json_in['data'])

    @staticmethod
    def from_component_json(json_in):
        """
        This method constructs a specific message component from the JSON returned by the get_component_json function.
        This method is intended to be overridden.

        Args:
            json_in (dict): The JSON representation of the component

        Returns:
            (MessageComponent): The constructed message component
        """
        return MessageComponent()


class Text(MessageComponent):
    """
    A MessageComponent used for rendering simple text.

    Args:
        text (str): The text to be rendered
    """

    def __init__(self, text):
        super(Text, self).__init__()
        self.text = text

    def get_component_json(self):
        """Gets the JSON representation of the component

        Returns:
            dict: The JSON representation of the component
        """
        return {'text': self.text}

    @staticmethod
    def from_component_json(json_in):
        """
        Constructs a Text component from JSON

        Args:
            json_in (dict): The JSON from which to construct the Text component

        Returns:
            (Text): The text component object
        """
        return Text(json_in['text'])


class Url(MessageComponent):
    """
    A MessageComponent used for rendering hyperlinks.

    Args:
        url (str): The URL of the link
        title (str, optional): The title to use for the link. Defaults to None.
    """

    def __init__(self, url, title=None):
        super(Url, self).__init__()
        self.url = url
        self.title = title

    def get_component_json(self):
        """Gets the JSON representation of the component

        Returns:
            dict: The JSON representation of the component
        """
        ret = {'url': self.url}
        if self.title:
            ret['title'] = self.title
        return ret

    @staticmethod
    def from_component_json(json_in):
        """
        Constructs a Url component from JSON

        Args:
            json_in (dict): The JSON from which to construct the Text component

        Returns:
            (Url): The text component
        """
        return Url(json_in['url'], title=json_in.get('title', None))


class AcceptDecline(MessageComponent):
    """
    A MessageComponent used for rendering a button to Accept or Decline some action
    """

    def __init__(self):
        super(AcceptDecline, self).__init__(requires_response=True)

    @staticmethod
    def from_component_json(json_in):
        """
        Constructs an AcceptDecline component from JSON

        Args:
            json_in (dict): The JSON from which to construct the Text component

        Returns:
            (AcceptDecline): The text component
        """
        return AcceptDecline()


class Message(object):
    """
    An object used to contain an entire message.

    Args:
        subject (str, optional): The subject of the message. Defaults to None
        body (list[MessageComponent]): The body of the message. Defaults to an empty body.
    """

    def __init__(self, subject=None, body=None):
        self.subject = subject
        self.body = body if body is not None else []

    def append(self, message_component):
        """
        Appends a message component to the body of the message.

        Args:
            message_component (MessageComponent): The message component to append
        """
        self.body.append(message_component)

    def extend(self, message_components):
        """
        Adds multiple message components to the body of the message.

        Args:
            message_components (iterable(MesageComponent)): Components to add to the body of the message
        """
        self.body.extend(message_components)

    def __add__(self, another_message):
        message_components = []
        message_components.extend(self.body)
        message_components.extend(another_message.body)
        return Message(subject=self.subject, body=message_components)

    def __len__(self):
        return len(self.body)

    def __iter__(self):
        return iter(self.body)

    def as_json(self):
        """
        Get the JSON representation of this message

        Returns:
            (dict): The JSON representation of this message
        """
        ret = {'body': [message_component.as_json() for message_component in self.body]}
        if self.subject:
            ret['subject'] = self.subject
        return ret

    @staticmethod
    def from_json(json_in):
        """
        Constructs a Message from its JSON representation

        Args:
            json_in (dict): The JSON representation of this message

        Returns:
            (Message): The constructed Message
        """
        return Message(subject=json_in.get('subject', None),
                       body=[MessageComponent.from_json(x) for x in json_in.get('body', [])])


def send_message(message, users=None, roles=None, requires_reauth=False):
    """
    Helper function used to send a message

    Args:
        message (Message): The message to send
        users (list[int], optional): The IDs of the users to send the message to. Defaults to [].
        roles (list[int], optional): The IDs of the roles to send the message to. Defaults to [].
        requires_reauth (bool, optional): Does this message require reauthorization. CURRENTLY NOT IMPLEMENTED.
    """
    users = users if users is not None else []
    roles = roles if roles is not None else []
    WalkoffEvent.CommonWorkflowSignal.send(
        message.as_json(), event=WalkoffEvent.SendMessage, users=users, roles=roles, requires_reauth=requires_reauth)
