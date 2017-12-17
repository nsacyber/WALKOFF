from core.events import WalkoffEvent


class MessageComponent(object):
    def __init__(self, message_type, requires_response=False):
        self.message_type = message_type
        self.requires_response = requires_response

    def as_json(self):
        return {'type': self.message_type, 'requires_response': self.requires_response, 'data': self.get_component_json()}

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
        super(AcceptDecline, self).__init__('accept_decline', requires_response=True)


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


def send_message(message, users=None, roles=None, requires_reauth=False):
    users = users if users is not None else []
    roles = roles if roles is not None else []
    WalkoffEvent.CommonWorkflowSignal.send(
        message.as_json(), event=WalkoffEvent.SendMessage, users=users, roles=roles, requires_reauth=requires_reauth)
