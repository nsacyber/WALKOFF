import zmq
from zmq import ZMQError

from walkoff.events import WalkoffEvent
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.multiprocessedexecutor.proto_helpers import convert_to_protobuf
import logging
import walkoff.config

logger = logging.getLogger(__name__)


class ZMQResultsSender(object):
    def __init__(self, execution_db, socket_id=None, client_secret_key=None, client_public_key=None,
                 server_public_key=None):
        """Initialize a WorkflowResultsHandler object, which will be sending results of workflow execution

        Args:
            execution_db (ExecutionDatabase): An ExecutionDatabase connection object
            socket_id (str): The ID for the results socket
            client_secret_key (str): The secret key for the client
            client_public_key (str): The public key for the client
            server_public_key (str): The public key for the server
        """
        self.results_sock = None

        if socket_id is not None:
            self.results_sock = zmq.Context().socket(zmq.PUSH)
            self.results_sock.identity = socket_id
            self.results_sock.curve_secretkey = client_secret_key
            self.results_sock.curve_publickey = client_public_key
            self.results_sock.curve_serverkey = server_public_key
            try:
                self.results_sock.connect(walkoff.config.Config.ZMQ_RESULTS_ADDRESS)
            except ZMQError:
                logger.exception(
                    'Workflow Results handler could not connect to {}!'.format(
                        walkoff.config.Config.ZMQ_RESULTS_ADDRESS))
                raise

        self.execution_db = execution_db

    def shutdown(self):
        """Shuts down the results socket and tears down the ExecutionDatabase
        """
        if self.results_sock:
            self.results_sock.close()
            self.execution_db.tear_down()

    def handle_event(self, workflow, sender, **kwargs):
        """Listens for the data_sent callback, which signifies that an execution element needs to trigger a
                callback in the main thread.

            Args:
                workflow (Workflow): The Workflow object that triggered the event
                sender (ExecutionElement): The execution element that sent the signal.
                kwargs (dict): Any extra data to send.
        """
        event = kwargs['event']

        if event in [WalkoffEvent.TriggerActionAwaitingData, WalkoffEvent.WorkflowPaused]:
            saved_workflow = SavedWorkflow.from_workflow(workflow)
            self.execution_db.session.add(saved_workflow)
            self.execution_db.session.commit()
        elif kwargs['event'] == WalkoffEvent.ConsoleLog:
            action = workflow.get_executing_action()
            sender = action

        if self.results_sock:
            packet_bytes = convert_to_protobuf(sender, workflow, **kwargs)
            self.results_sock.send(packet_bytes)
        else:
            event.send(sender, data=kwargs.get('data', None))
