from unittest import TestCase
from apps.messaging import *
from walkoff.core.events import WalkoffEvent


class TestMessage(TestCase):

    def tearDown(self):
        for class_name in ('message_type1', 'message_type2'):
            MessageComponent.registry.pop(class_name, None)

    def test_class_name_to_tag(self):
        self.assertEqual(convert_class_name_to_tag('Camel'), 'camel')
        self.assertEqual(convert_class_name_to_tag('CamelCase'), 'camel_case')
        self.assertEqual(convert_class_name_to_tag('CamelCamelCase'), 'camel_camel_case')
        self.assertEqual(convert_class_name_to_tag('Camel2Camel2Case'), 'camel2_camel2_case')
        self.assertEqual(convert_class_name_to_tag('getHTTPResponseCode'), 'get_http_response_code')
        self.assertEqual(convert_class_name_to_tag('get2HTTPResponseCode'), 'get2_http_response_code')
        self.assertEqual(convert_class_name_to_tag('HTTPResponseCodeXYZ'), 'http_response_code_xyz')

    def test_registry(self):

        class MessageType1(MessageComponent): pass
        self.assertEqual(MessageType1.message_type, convert_class_name_to_tag(MessageType1.__name__))
        self.assertEqual(MessageComponent.registry[MessageType1.message_type], MessageType1)
        class MessageType2(MessageComponent): pass
        self.assertEqual(MessageType2.message_type, convert_class_name_to_tag(MessageType2.__name__))
        self.assertEqual(MessageComponent.registry[MessageType2.message_type], MessageType2)

    def test_registry_duplicate(self):

        class MessageType1(MessageComponent): pass
        original_class = MessageType1
        class MessageType1(MessageComponent): pass
        self.assertEqual(MessageComponent.registry['message_type1'], original_class)

    def test_message_component_init(self):
        message_component = MessageComponent()
        self.assertEqual(message_component.message_type, '__base')
        self.assertFalse(message_component.requires_response)

    def test_message_component_init_requires_response(self):
        message_component = MessageComponent(requires_response=True)
        self.assertTrue(message_component.requires_response)

    def test_message_component_get_component_json(self):
        message_component = MessageComponent()
        self.assertDictEqual(message_component.get_component_json(), {})

    def test_message_component_as_json(self):
        message_component = MessageComponent()
        self.assertDictEqual(message_component.as_json(), {'type': '__base', 'requires_response': False, 'data': {}})

    def test_message_component_requires_response_as_json(self):
        message_component = MessageComponent(requires_response=True)
        self.assertDictEqual(message_component.as_json(), {'type': '__base', 'requires_response': True, 'data': {}})

    def test_message_component_from_component_json(self):
        self.assertIsInstance(MessageComponent.from_component_json({}), MessageComponent)
        self.assertIsInstance(MessageComponent.from_component_json({'a': 'b'}), MessageComponent)

    def test_message_component_from_json_unknown_type(self):
        json_in = {'type': 'invalid', 'requires_response': True, 'data': {'a': 42}}
        self.assertIsInstance(MessageComponent.from_json(json_in), MessageComponent)

    def test_message_component_from_json(self):
        class MessageType1(MessageComponent):
            def __init__(self, a):
                super(MessageType1, self).__init__()
                self.a = a

            @staticmethod
            def from_component_json(json_in):
                return MessageType1(json_in['a'])

        json_in = {'type': MessageType1.message_type, 'requires_response': True, 'data': {'a': 42}}
        generated = MessageComponent.from_json(json_in)
        self.assertIsInstance(generated, MessageType1)
        self.assertEqual(generated.a, 42)

    def test_text_component_init(self):
        text = Text('some text here')
        self.assertEqual(text.message_type, 'text')
        self.assertEqual(text.text, 'some text here')
        self.assertIsInstance(text, MessageComponent)

    def test_text_component_get_component_json(self):
        text = Text('some text here')
        self.assertDictEqual(text.get_component_json(), {'text': 'some text here'})

    def test_text_from_component_json(self):
        text = Text.from_component_json({'text': 'something'})
        self.assertEqual(text.text, 'something')

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

    def test_url_component_from_component_json(self):
        url = Url.from_component_json({'url': 'a.b.c'})
        self.assertEqual(url.url, 'a.b.c')
        self.assertIsNone(url.title)

    def test_url_component_from_component_json_with_title(self):
        url = Url.from_component_json({'url': 'a.b.c', 'title': 'click here'})
        self.assertEqual(url.url, 'a.b.c')
        self.assertEqual(url.title, 'click here')

    def test_accept_decline_component_init(self):
        accept_decline = AcceptDecline()
        self.assertEqual(accept_decline.message_type, 'accept_decline')
        self.assertTrue(accept_decline.requires_response)

    def test_accept_decline_component_get_component_json(self):
        accept_decline = AcceptDecline()
        self.assertDictEqual(accept_decline.get_component_json(), {})

    def test_accept_decline_from_component_json(self):
        accept_decline = AcceptDecline.from_component_json({})
        self.assertIsInstance(accept_decline, AcceptDecline)

    def test_message_init_(self):
        message = Message()
        self.assertListEqual(message.body, [])
        self.assertIsNone(message.subject)

    def test_message_init_with_subject(self):
        message = Message(subject='Important')
        self.assertListEqual(message.body, [])
        self.assertEqual(message.subject, 'Important')

    def test_message_init_with_initial_components(self):
        components = [AcceptDecline(), Text('a')]
        message = Message(components=components)
        self.assertListEqual(message.body, components)

    def test_message_append_empty_message(self):
        message = Message()
        component = AcceptDecline()
        message.append(component)
        self.assertEqual(len(message.body), 1)
        self.assertEqual(message.body[0], component)

    def test_message_append(self):
        components = [AcceptDecline(), Text('a')]
        message = Message(components=components)
        component = Text('b')
        message.append(component)
        self.assertEqual(len(message.body), 3)
        self.assertEqual(message.body[2], component)

    def test_message_extend_empty_message(self):
        message = Message()
        components = [AcceptDecline(), Text('a')]
        message.extend(components)
        self.assertEqual(len(message.body), 2)
        self.assertEqual(message.body, components)

    def test_message_extend(self):
        components = [AcceptDecline(), Text('a')]
        message = Message(components=components)
        new_components = [Text('a'), Text('b')]
        message.extend(new_components)
        self.assertEqual(len(message.body), 4)

    def test_message_extend_empty_components(self):
        components = [AcceptDecline(), Text('a')]
        message = Message(components=components)
        message.extend([])
        self.assertEqual(len(message.body), 2)

    def test_message_add(self):
        components1 = [Text('a'), Text('b')]
        components2 = [AcceptDecline(), Text('c'), Text('d')]
        message1 = Message(components=components1, subject='some subject')
        message2 = Message(components=components2)
        message = message1 + message2
        self.assertEqual(len(message.body), 5)
        self.assertEqual(message.subject, 'some subject')

    def test_message_length(self):
        components = [Text('a'), Text('b')]
        message = Message(components=components)
        self.assertEqual(len(message), 2)

    def test_message_as_json(self):
        components = [Text('a'), Text('b')]
        message = Message(components=components)
        self.assertDictEqual(message.as_json(), {'body': [component.as_json() for component in components]})

    def test_message_as_json_with_subject(self):
        components = [Text('a'), Text('b')]
        message = Message(components=components, subject='important!')
        self.assertDictEqual(message.as_json(),
                             {'subject': 'important!', 'body': [component.as_json() for component in components]})

    def test_message_from_json(self):
        components = [Text('a'), Text('b')]
        message = Message(components=components)
        message = Message.from_json(message.as_json())
        for component in message.body:
            self.assertIn(component.text, ('a', 'b'))
        self.assertIsNone(message.subject)

    def test_message_from_json_with_subject(self):
        components = [Text('a'), Text('b')]
        message = Message(components=components, subject='important!')
        message = Message.from_json(message.as_json())
        for component in message.body:
            self.assertIn(component.text, ('a', 'b'))
        self.assertEqual(message.subject, 'important!')

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
        self.assertDictEqual(data['sender'], message.as_json())
        self.assertEqual(data['data']['event'], WalkoffEvent.SendMessage)
        self.assertListEqual(data['data']['users'], [1, 2, 3])
        self.assertFalse(data['data']['requires_reauth'])
