import logging

import zmq
from zmq import ZMQError

import walkoff.config
from walkoff.events import WalkoffEvent
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.multiprocessedexecutor.protoconverter import ProtobufWorkflowResultsConverter, \
    ProtobufWorkflowCommunicationConverter

logger = logging.getLogger(__name__)


class ZmqWorkflowResultsSender(object):
    def __init__(self, execution_db, message_converter=ProtobufWorkflowResultsConverter, socket_id=None):
        """Initialize a WorkflowResultsHandler object, which will be sending results of workflow execution

        Args:
            execution_db (ExecutionDatabase): An ExecutionDatabase connection object
            socket_id (str): The ID for the results socket
            message_converter (ProtobufWorkflowResultsConverter): The class to convert messages
        """
        self._ready = False
        self.results_sock = None

        if socket_id is not None:
            self.results_sock = zmq.Context().socket(zmq.PUSH)
            self.results_sock.identity = socket_id
            self.results_sock.curve_secretkey = walkoff.config.Config.CLIENT_PRIVATE_KEY
            self.results_sock.curve_publickey = walkoff.config.Config.CLIENT_PUBLIC_KEY
            self.results_sock.curve_serverkey = walkoff.config.Config.SERVER_PUBLIC_KEY
            try:
                self.results_sock.connect(walkoff.config.Config.ZMQ_RESULTS_ADDRESS)
            except ZMQError:
                logger.exception(
                    'Workflow Results handler could not connect to {}!'.format(
                        walkoff.config.Config.ZMQ_RESULTS_ADDRESS))
                raise

        self.execution_db = execution_db
        self.message_converter = message_converter

        if self.check_status():
            self._ready = True

    def shutdown(self):
        """Shuts down the results socket and tears down the ExecutionDatabase
        """
        self._ready = False
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
            packet_bytes = self.message_converter.event_to_protobuf(sender, workflow, **kwargs)
            self.results_sock.send(packet_bytes)
        else:
            event.send(sender, data=kwargs.get('data', None))

    def is_ready(self):
        return self._ready

    def check_status(self):
        if self.results_sock:
            return True

    def send_ready_message(self):
        WalkoffEvent.CommonWorkflowSignal.send(sender={'id': self.results_sock.identity},
                                               event=WalkoffEvent.WorkerReady)

    def create_workflow_request_message(self, workflow_id, workflow_execution_id, start=None, start_arguments=None,
                                        resume=False, environment_variables=None, user=None):
        return self.message_converter.create_workflow_request_message(workflow_id, workflow_execution_id, start,
                                                                      start_arguments, resume, environment_variables,
                                                                      user)


class ZmqWorkflowCommunicationSender(object):

    def __init__(self, message_converter=ProtobufWorkflowCommunicationConverter):
        self.comm_socket = zmq.Context.instance().socket(zmq.PUB)
        self.comm_socket.curve_secretkey = walkoff.config.Config.SERVER_PRIVATE_KEY
        self.comm_socket.curve_publickey = walkoff.config.Config.SERVER_PUBLIC_KEY
        self.comm_socket.curve_server = True
        self.comm_socket.bind(walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS)

        self.message_converter = message_converter

    def shutdown(self):
        self.comm_socket.close()

    def pause_workflow(self, workflow_execution_id):
        """Pauses a workflow currently executing.

        Args:
            workflow_execution_id (UUID): The execution ID of the workflow.
        """
        logger.info('Pausing workflow {0}'.format(workflow_execution_id))
        self._send_message(self.message_converter.create_workflow_pause_message(workflow_execution_id))

    def abort_workflow(self, workflow_execution_id):
        """Aborts a workflow currently executing.

        Args:
            workflow_execution_id (UUID): The execution ID of the workflow.
        """
        logger.info('Aborting running workflow {0}'.format(workflow_execution_id))
        self._send_message(self.message_converter.create_workflow_abort_message(workflow_execution_id))

    def send_exit_to_workers(self):
        """Sends the exit message over the communication sockets, otherwise worker receiver threads will hang"""
        self._send_message(self.message_converter.create_worker_exit_message())

    def _send_message(self, message):
        self.comm_socket.send(message)
