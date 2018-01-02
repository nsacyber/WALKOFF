from walkoff.events import WalkoffEvent
import re
import logging
from six import add_metaclass

__all__ = ['Text', 'Url', 'AcceptDecline', 'Message', 'send_message']

logger = logging.getLogger(__name__)


def convert_class_name_to_tag(name):
    sub = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', sub).lower()


class MessageComponentTypeRegistry(type):
    def __init__(cls, name, bases, dct):
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
    def __init__(self, requires_response=False):
        self.requires_response = requires_response

    def as_json(self):
        return {'type': self.message_type, 'requires_response': self.requires_response,
                'data': self.get_component_json()}

    def get_component_json(self):
        return {}

    @staticmethod
    def from_json(json_in):
        message_component_class = MessageComponent.registry.get(json_in['type'], MessageComponent)
        return message_component_class.from_component_json(json_in['data'])

    @staticmethod
    def from_component_json(json_in):
        return MessageComponent()


class Text(MessageComponent):
    def __init__(self, text):
        super(Text, self).__init__()
        self.text = text

    def get_component_json(self):
        return {'text': self.text}

    @staticmethod
    def from_component_json(json_in):
        return Text(json_in['text'])


class Url(MessageComponent):
    def __init__(self, url, title=None):
        super(Url, self).__init__()
        self.url = url
        self.title = title

    def get_component_json(self):
        ret = {'url': self.url}
        if self.title:
            ret['title'] = self.title
        return ret

    @staticmethod
    def from_component_json(json_in):
        return Url(json_in['url'], title=json_in.get('title', None))


class AcceptDecline(MessageComponent):
    def __init__(self):
        super(AcceptDecline, self).__init__(requires_response=True)

    @staticmethod
    def from_component_json(json_in):
        return AcceptDecline()


class Message(object):
    def __init__(self, subject=None, components=None):
        self.subject = subject
        self.body = components if components is not None else []

    def append(self, message_component):
        self.body.append(message_component)

    def extend(self, message_components):
        self.body.extend(message_components)

    def __add__(self, another_message):
        message_components = []
        message_components.extend(self.body)
        message_components.extend(another_message.body)
        return Message(subject=self.subject, components=message_components)

    def __len__(self):
        return len(self.body)

    def __iter__(self):
        return iter(self.body)

    def as_json(self):
        ret = {'body': [message_component.as_json() for message_component in self.body]}
        if self.subject:
            ret['subject'] = self.subject
        return ret

    @staticmethod
    def from_json(json_in):
        return Message(subject=json_in.get('subject', None),
                       components=[MessageComponent.from_json(x) for x in json_in.get('body', [])])


def send_message(message, users=None, roles=None, requires_reauth=False):
    users = users if users is not None else []
    roles = roles if roles is not None else []
    WalkoffEvent.CommonWorkflowSignal.send(
        message.as_json(), event=WalkoffEvent.SendMessage, users=users, roles=roles, requires_reauth=requires_reauth)
