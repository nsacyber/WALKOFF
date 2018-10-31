from unittest import TestCase

from apps import App as AppBase
from tests.util import execution_db_help
from tests.util import initialize_test_config
from walkoff.executiondb.device import App, Device, DeviceField, EncryptedDeviceField
from tests.util.mock_objects import MockRedisCacheAdapter
from uuid import uuid4
import dill


class TestAppBase(TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        cls.execution_db = execution_db_help.setup_dbs()
        cls.cache = MockRedisCacheAdapter()

    @classmethod
    def tearDownClass(cls):
        execution_db_help.tear_down_execution_db()

    def setUp(self):
        self.test_app_name = 'TestApp'
        self.device1 = Device('test', [], [], 'type1')
        plaintext_fields = [DeviceField('test_name', 'integer', 123), DeviceField('test2', 'string', 'something')]
        encrypted_fields = [EncryptedDeviceField('test3', 'boolean', True),
                            EncryptedDeviceField('test4', 'string', 'something else')]
        self.device2 = Device('test2', plaintext_fields, encrypted_fields, 'type2')
        self.db_app = App(self.test_app_name, [self.device1, self.device2])

        self.execution_db.session.add(self.db_app)
        self.execution_db.session.commit()

    def tearDown(self):
        self.execution_db.session.rollback()
        for device in self.execution_db.session.query(Device).all():
            self.execution_db.session.delete(device)
        for field in self.execution_db.session.query(DeviceField).all():
            self.execution_db.session.delete(field)
        for field in self.execution_db.session.query(EncryptedDeviceField).all():
            self.execution_db.session.delete(field)
        app = self.execution_db.session.query(App).filter(App.name == self.test_app_name).first()
        if app is not None:
            self.execution_db.session.delete(app)
        self.execution_db.session.commit()
        self.cache.clear()

    def test_app_is_tagged(self):
        self.assertTrue(getattr(AppBase, '_is_walkoff_app', False))

    def test_init(self):
        app = AppBase(self.test_app_name, self.device1.id, {})
        self.assertEqual(app.app, self.db_app)
        self.assertEqual(app.device, self.device1)
        self.assertDictEqual(app.device_fields, {})
        self.assertEqual(app.device_type, 'type1')
        self.assertEqual(app.device_id, self.device1.id)

    def test_init_with_fields(self):
        app = AppBase(self.test_app_name, self.device2.id, {})
        self.assertEqual(app.app, self.db_app)
        self.assertEqual(app.device, self.device2)
        self.assertDictEqual(app.device_fields, self.device2.get_plaintext_fields())
        self.assertEqual(app.device_type, 'type2')
        self.assertEqual(app.device_id, self.device2.id)

    def test_init_with_invalid_app(self):
        app = AppBase('Invalid', self.device2.id, {})
        self.assertIsNone(app.app)
        self.assertIsNone(app.device)
        self.assertDictEqual(app.device_fields, {})
        self.assertEqual(app.device_type, None)
        self.assertEqual(app.device_id, self.device2.id)

    def test_init_with_invalid_device(self):
        app = AppBase(self.test_app_name, 'invalid', {})
        self.assertEqual(app.app, self.db_app)
        self.assertIsNone(app.device)
        self.assertDictEqual(app.device_fields, {})
        self.assertEqual(app.device_type, None)
        self.assertEqual(app.device_id, 'invalid')

    def test_get_all_devices(self):
        app = AppBase(self.test_app_name, self.device2.id, {})
        devices = app.get_all_devices()
        self.assertIn(self.device1, devices)
        self.assertIn(self.device2, devices)

    def test_get_all_devices_invalid_app(self):
        app = AppBase('Invalid', self.device2.id, {})
        self.assertListEqual(app.get_all_devices(), [])

    def test_setattr_syncs_to_cache(self):
        workflow_id = uuid4()
        context = {'workflow_execution_id': workflow_id}
        app = AppBase('Something', self.device2.id, context)
        app._cache = self.cache
        app.foo = 42
        app.bar = 23
        self.assertSetEqual(
            set(self.cache.scan()),
            {app._format_cache_key('foo'), app._format_cache_key('bar')}
        )
        for field, expected in (('foo', 42), ('bar', 23)):
            self.assertEqual(dill.loads(self.cache.get(app._format_cache_key(field))), expected)

    def test_getattr_gets_from_cache(self):
        workflow_id = uuid4()
        context = {'workflow_execution_id': workflow_id}
        app = AppBase('Something', self.device2.id, context)
        app._cache = self.cache
        app.foo = 42
        app.bar = 23
        self.cache.set(app._format_cache_key('foo'), dill.dumps('a'))
        self.cache.set(app._format_cache_key('bar'), dill.dumps('b'))
        self.assertEqual(app.foo, 'a')
        self.assertEqual(app.bar, 'b')
        with self.assertRaises(AttributeError):
            y = app.baz

    def test_reset_context(self):
        workflow_id1 = uuid4()
        context1 = {'workflow_execution_id': workflow_id1}
        app1 = AppBase('Something', self.device2.id, context1)
        app1._cache = self.cache
        workflow_id2 = uuid4()
        context2 = {'workflow_execution_id': workflow_id2}
        app2 = AppBase('Something', self.device2.id, context2)
        app2._cache = self.cache
        app1.foo = 42
        app1.bar = 'abc'
        app2.foo = 43
        app2.bar = 'def'
        app1._reset_context(context2)
        self.assertEqual(app1.foo, 43)
        self.assertEqual(app1.bar, 'def')

    def test_from_cache(self):
        class Foo(AppBase):
            def __init__(self, app, device, context):
                super(Foo, self).__init__(app, device, context)
                self.a = 4
                self.b = 'a'

        workflow_id = uuid4()
        context = {'workflow_execution_id': workflow_id}
        app = Foo('Something', self.device2.id, context)
        app.a = 5
        app.b = 'b'

        reconstructed = Foo.from_cache('Something', self.device2.id, context)
        self.assertIsInstance(reconstructed, Foo)
        self.assertEqual(reconstructed.a, 5)
        self.assertEqual(reconstructed.b, 'b')

