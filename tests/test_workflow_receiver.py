from unittest import TestCase
from walkoff.multiprocessedexecutor.worker import WorkflowReceiver
import nacl.bindings.crypto_box
from nacl.public import PrivateKey
from walkoff.config import Config
from zmq import auth
import walkoff.cache
from mock import patch, create_autospec
from tests.util.mock_objects import MockRedisCacheAdapter
import os.path


class TestWorkflowReceiver(TestCase):

    @classmethod
    def setUpClass(cls):
        server_secret_file = os.path.join(Config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)
        client_secret_file = os.path.join(Config.ZMQ_PRIVATE_KEYS_PATH, "client.key_secret")
        client_public, client_secret = auth.load_certificate(client_secret_file)
        cls.key = PrivateKey(client_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES])
        cls.server_key = PrivateKey(server_secret[:nacl.bindings.crypto_box_SECRETKEYBYTES]).public_key

    @patch.object(walkoff.cache, 'make_cache', return_value=MockRedisCacheAdapter())
    def test_init(self, mock_make_cache):
        receiver = WorkflowReceiver(self.key, self.server_key, Config.CACHE)
        self.assertEqual(receiver.key, self.key)
        self.assertEqual(receiver.server_key, self.server_key)
        mock_make_cache.assert_called_once_with(Config.CACHE)
        self.assertIsInstance(receiver.cache, MockRedisCacheAdapter)
        self.assertFalse(receiver.exit)

    @patch.object(walkoff.cache, 'make_cache', return_value=MockRedisCacheAdapter())
    def get_receiver(self, mock_create_cache):
        return WorkflowReceiver(self.key, self.server_key, Config.CACHE)

    def test_shutdown(self):
        receiver = self.get_receiver()
        with patch.object(receiver.cache, 'shutdown') as mock_shutdown:
            receiver.shutdown()
            self.assertTrue(receiver.exit)
            mock_shutdown.assert_called_once()

    def test_receive_workflow_no_message(self):
        receiver = self.get_receiver()
        workflow_generator = receiver.receive_workflows()
        workflow = next(workflow_generator)
        self.assertIsNone(workflow)
