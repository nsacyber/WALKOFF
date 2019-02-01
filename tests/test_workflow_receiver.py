import os.path
from unittest import TestCase
from uuid import uuid4

import nacl.bindings.crypto_box
from mock import patch
from nacl.public import PrivateKey, Box
from zmq import auth

import walkoff.cache
import walkoff.config
from tests.util import initialize_test_config, execution_db_help
from tests.util.mock_objects import MockRedisCacheAdapter
from walkoff.executiondb.argument import Argument
from walkoff.server.app import create_app
from walkoff.proto.build.data_pb2 import ExecuteWorkflowMessage
from walkoff.worker.zmq_workflow_receivers import WorkflowReceiver
from walkoff.multiprocessedexecutor.protoconverter import ProtobufWorkflowResultsConverter


class TestWorkflowReceiver(TestCase):

    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        cls.app = create_app(walkoff.config.Config)
        cls.context = cls.app.test_request_context()
        cls.context.push()

        server_secret_file = os.path.join(walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)
        client_secret_file = os.path.join(walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH, "client.key_secret")
        client_public, client_secret = auth.load_certificate(client_secret_file)
        cls.key = PrivateKey(client_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES])
        cls.server_key = PrivateKey(server_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES]).public_key
        cls.box = Box(cls.key, cls.server_key)

    def setUp(self):
        execution_db_help.setup_dbs()

    def tearDown(self):
        execution_db_help.cleanup_execution_db()
        execution_db_help.tear_down_execution_db()

    @patch.object(walkoff.cache, 'make_cache', return_value=MockRedisCacheAdapter())
    def test_init(self, mock_make_cache):
        receiver = WorkflowReceiver(self.key, self.server_key, walkoff.config.Config.CACHE)
        self.assertEqual(receiver.key, self.key)
        self.assertEqual(receiver.server_key, self.server_key)
        mock_make_cache.assert_called_once_with(walkoff.config.Config.CACHE)
        self.assertIsInstance(receiver.cache, MockRedisCacheAdapter)
        self.assertFalse(receiver._exit)

    @patch.object(walkoff.cache, 'make_cache', return_value=MockRedisCacheAdapter())
    def get_receiver(self, mock_create_cache):
        return WorkflowReceiver(self.key, self.server_key, walkoff.config.Config.CACHE)

    def test_shutdown(self):
        receiver = self.get_receiver()
        with patch.object(receiver.cache, 'shutdown') as mock_shutdown:
            receiver.shutdown()
            self.assertTrue(receiver._exit)
            mock_shutdown.assert_called_once()

    def test_receive_workflow_no_message(self):
        receiver = self.get_receiver()
        workflow_generator = receiver.receive_workflows()
        workflow = next(workflow_generator)
        self.assertIsNone(workflow)

    def check_workflow_message(self, message, expected):
        receiver = self.get_receiver()
        encrypted_message = self.box.encrypt(message.SerializeToString())
        workflow_generator = receiver.receive_workflows()
        receiver.cache.lpush('request_queue', encrypted_message)
        workflow = next(workflow_generator)
        self.assertTupleEqual(workflow, expected)

    def test_receive_workflow_basic_workflow(self):
        workflow_id = str(uuid4())
        execution_id = str(uuid4())
        message = ExecuteWorkflowMessage()
        message.workflow_id = workflow_id
        message.workflow_execution_id = execution_id
        message.resume = True
        self.check_workflow_message(message, (workflow_id, execution_id, '', [], True, [], ''))

    def test_receive_workflow_with_start(self):
        workflow_id = str(uuid4())
        execution_id = str(uuid4())
        start = str(uuid4())
        message = ExecuteWorkflowMessage()
        message.workflow_id = workflow_id
        message.workflow_execution_id = execution_id
        message.resume = True
        message.start = start
        self.check_workflow_message(message, (workflow_id, execution_id, start, [], True, [], ''))

    def test_receive_workflow_with_arguments(self):
        workflow_id = str(uuid4())
        execution_id = str(uuid4())
        start = str(uuid4())
        ref = str(uuid4())
        arguments = [Argument('arg1', value=42),
                     Argument('arg2', reference=ref, selection=[Argument('test', 'a'), Argument('test', 1)])]

        message = ExecuteWorkflowMessage()
        message.workflow_id = workflow_id
        message.workflow_execution_id = execution_id
        message.resume = True
        message.start = start

        ProtobufWorkflowResultsConverter._add_arguments_to_proto(message.arguments, arguments)

        receiver = self.get_receiver()
        encrypted_message = self.box.encrypt(message.SerializeToString())
        workflow_generator = receiver.receive_workflows()
        receiver.cache.lpush('request_queue', encrypted_message)
        workflow = next(workflow_generator)
        workflow_arguments = workflow[3]
        self.assertEqual(workflow_arguments[0].name, arguments[0].name)
        self.assertEqual(workflow_arguments[0].value, str(arguments[0].value))
        self.assertEqual(workflow_arguments[1].name, arguments[1].name)
        self.assertEqual(str(workflow_arguments[1].reference), ref)
        self.assertEqual(len(workflow_arguments[1].selection), len(arguments[1].selection))

    def test_receive_workflow_exit(self):
        receiver = self.get_receiver()
        workflow_generator = receiver.receive_workflows()
        receiver._exit = True
        with self.assertRaises(StopIteration):
            next(workflow_generator)

    def test_receive_workflow_with_env_vars(self):
        workflow_id = str(uuid4())
        execution_id = str(uuid4())
        start = str(uuid4())
        env_var_id = str(uuid4())
        env_var_id2 = str(uuid4())
        env_vars = [{"id": env_var_id, "value": "env_var_1"}, {"id": env_var_id2, "value": "env_var_2"}]
        message = ExecuteWorkflowMessage()
        message.workflow_id = workflow_id
        message.workflow_execution_id = execution_id
        message.resume = True
        message.start = start
        env_var = message.environment_variables.add()
        env_var.id = env_vars[0]['id']
        env_var.value = env_vars[0]['value']
        env_var = message.environment_variables.add()
        env_var.id = env_vars[1]['id']
        env_var.value = env_vars[1]['value']

        receiver = self.get_receiver()
        encrypted_message = self.box.encrypt(message.SerializeToString())
        workflow_generator = receiver.receive_workflows()
        receiver.cache.lpush('request_queue', encrypted_message)
        workflow = next(workflow_generator)
        workflow_env_vars = workflow[5]
        self.assertEqual(str(workflow_env_vars[0].id), env_vars[0]['id'])
        self.assertEqual(workflow_env_vars[0].value, env_vars[0]['value'])
        self.assertEqual(str(workflow_env_vars[1].id), env_vars[1]['id'])
        self.assertEqual(workflow_env_vars[1].value, env_vars[1]['value'])
