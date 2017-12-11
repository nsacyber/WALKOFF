from unittest import TestCase
from apps.messaging import *
from core.events import WalkoffEvent

class TestMessage(TestCase):

    def test_message_component_init(self):
        message_component = MessageComponent('some type')
        self.assertEqual(message_component.message_type, 'some type')
        self.assertFalse(message_component.requires_auth)

    def test_message_component_init_requires_auth(self):
        message_component = MessageComponent('some type', requires_auth=True)
        self.assertEqual(message_component.message_type, 'some type')
        self.assertTrue(message_component.requires_auth)

    def test_message_component_get_component_json(self):
        message_component = MessageComponent('some type')
        self.assertDictEqual(message_component.get_component_json(), {})

    def test_message_component_as_json(self):
        message_component = MessageComponent('some type')
        self.assertDictEqual(message_component.as_json(), {'type': 'some type', 'requires_auth': False, 'data': {}})

    def test_message_component_requires_auth_as_json(self):
        message_component = MessageComponent('some type',requires_auth=True)
        self.assertDictEqual(message_component.as_json(), {'type': 'some type', 'requires_auth': True, 'data': {}})

    def test_text_component_init(self):
        text = Text('some text here')
        self.assertEqual(text.message_type, 'text')
        self.assertEqual(text.text, 'some text here')
        self.assertIsInstance(text, MessageComponent)

    def test_text_component_get_component_json(self):
        text = Text('some text here')
        self.assertDictEqual(text.get_component_json(), {'text': 'some text here'})

    def test_url_component_init(self):
        url = Url('some.url.goes.here.com')
        self.assertEqual(url.message_type, 'url')
        self.assertEqual(url.url, 'some.url.goes.here.com')
        self.assertIsNone(url.title)
        self.assertIsInstance(url, MessageComponent)

    def test_url_component_init_with_title(self):
        url = Url('some.url.goes.here.com', title='Some Better Title')
        self.assertEqual(url.message_type, 'url')
        self.assertEqual(url.url, 'some.url.goes.here.com')
        self.assertEqual(url.title, 'Some Better Title')
        self.assertIsInstance(url, MessageComponent)

    def test_url_component_get_component_json(self):
        url = Url('some.url.goes.here.com')
        self.assertDictEqual(url.get_component_json(), {'url': 'some.url.goes.here.com'})

    def test_url_component_with_title_get_component_json(self):
        url = Url('some.url.goes.here.com', title='Click Here')
        self.assertDictEqual(url.get_component_json(), {'url': 'some.url.goes.here.com', 'title': 'Click Here'})

    def test_accept_decline_component_init(self):
        accept_decline = AcceptDecline()
        self.assertEqual(accept_decline.message_type, 'accept_decline')
        self.assertTrue(accept_decline.requires_auth)

    def test_accept_decline_component_get_component_json(self):
        accept_decline = AcceptDecline()
        self.assertDictEqual(accept_decline.get_component_json(), {})

    def test_message_init_(self):
        message = Message()
        self.assertListEqual(message.message, [])

    def test_message_init_with_initial_components(self):
        components = [AcceptDecline(), Text('a')]
        message = Message(components=components)
        self.assertListEqual(message.message, components)

    def test_message_append_empty_message(self):
        message = Message()
        component = AcceptDecline()
        message.append(component)
        self.assertEqual(len(message.message), 1)
        self.assertEqual(message.message[0], component)

    def test_message_append(self):
        components = [AcceptDecline(), Text('a')]
        message = Message(components=components)
        component = Text('b')
        message.append(component)
        self.assertEqual(len(message.message), 3)
        self.assertEqual(message.message[2], component)

    def test_message_extend_empty_message(self):
        message = Message()
        components = [AcceptDecline(), Text('a')]
        message.extend(components)
        self.assertEqual(len(message.message), 2)
        self.assertEqual(message.message, components)

    def test_message_extend(self):
        components = [AcceptDecline(), Text('a')]
        message = Message(components=components)
        new_components = [Text('a'), Text('b')]
        message.extend(new_components)
        self.assertEqual(len(message.message), 4)

    def test_message_extend_empty_components(self):
        components = [AcceptDecline(), Text('a')]
        message = Message(components=components)
        message.extend([])
        self.assertEqual(len(message.message), 2)

    def test_message_add(self):
        components1 = [Text('a'), Text('b')]
        components2 = [AcceptDecline(), Text('c'), Text('d')]
        message1 = Message(components=components1)
        message2 = Message(components=components2)
        message = message1 + message2
        self.assertEqual(len(message.message), 5)

    def test_message_length(self):
        components = [Text('a'), Text('b')]
        message = Message(components=components)
        self.assertEqual(len(message), 2)

    def test_message_as_json(self):
        components = [Text('a'), Text('b')]
        message = Message(components=components)
        self.assertDictEqual(message.as_json(), {'message': [component.as_json() for component in components]})

    def test_message_iterator(self):
        components = [Text('a'), Text('b')]
        message = Message(components=components)
        self.assertEqual(list(message), components)

    def test_send_message(self):

        data = {'called': False}

        @WalkoffEvent.CommonWorkflowSignal.connect
        def receive(sender, **kwargs):
            data['called'] = True
            data['sender'] = sender
            data['data'] = kwargs

        components = [Text('a'), Text('b')]
        message = Message(components=components)
        send_message(message, [1, 2, 3])
        self.assertTrue(data['called'])
        self.assertIs(data['sender'], message)
        self.assertEqual(data['data']['event'], WalkoffEvent.SendMessage)
        self.assertListEqual(data['data']['users'], [1, 2, 3])
        self.assertFalse(data['data']['requires_reauth'])
