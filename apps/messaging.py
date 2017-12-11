from core.events import WalkoffEvent


class MessageComponent(object):
    def __init__(self, message_type):
        self.message_type = message_type

    def as_json(self):
        return {'type': self.message_type, 'data': self.get_component_json()}

    def get_component_json(self):
        return {}


class Text(MessageComponent):

    def __init__(self, text):
        super(Text, self).__init__('text')
        self.text = text

    def get_component_json(self):
        return {'text': self.text}


class Url(MessageComponent):
    def __init__(self, url, title=None):
        super(Url, self).__init__('url')
        self.url = url
        self.title = title

    def get_component_json(self):
        ret = {'url': self.url}
        if self.title:
            ret['title'] = self.title
        return ret


class AcceptDecline(MessageComponent):

    def __init__(self):
        super(AcceptDecline, self).__init__('accept_decline')


class Message(object):
    def __init__(self, components=None):
        self.message = components if components is not None else []

    def append(self, message_component):
        self.message.append(message_component)

    def extend(self, message_components):
        self.message.extend(message_components)

    def __add__(self, another_message):
        messages = []
        messages.extend(self.message)
        messages.extend(another_message.message)
        return Message(components=messages)

    def __len__(self):
        return len(self.message)

    def __iter__(self):
        return iter(self.message)

    def as_json(self):
        return {'message': [message_component.as_json() for message_component in self.message]}


def send_message(message, users, requires_reauth=False):
    WalkoffEvent.CommonWorkflowSignal.send(
        message, event=WalkoffEvent.SendMessage, users=users, requires_reauth=requires_reauth)
