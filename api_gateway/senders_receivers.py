import json
import logging

import gevent
from redis import Redis

from api_gateway.config import Config
from api_gateway.events import WalkoffEvent

logger = logging.getLogger(__name__)


class WorkflowResultsSender(object):
    def __init__(self, execution_db):
        """Initialize a WorkflowResultsHandler object, which will be sending results of workflow execution

        Args:
            execution_db (ExecutionDatabase): An ExecutionDatabase connection object

        """
        self._ready = False
        self.execution_db = execution_db

    def shutdown(self):
        """Shuts down the results socket and tears down the ExecutionDatabase
        """
        self._ready = False
        self.execution_db.tear_down()

    def handle_event(self, workflow, sender, **kwargs):
        """Listens for the data_sent callback, which signifies that an execution element needs to trigger a
                callback in the main thread.

            Args:
                workflow (Workflow|WorkflowExecutionContext): The Workflow object that triggered the event
                sender (ExecutionElement): The execution element that sent the signal.
                kwargs (dict): Any extra data to send.
        """
        event = kwargs['event']

        if event in [WalkoffEvent.TriggerActionAwaitingData, WalkoffEvent.WorkflowPaused]:
            pass
        elif kwargs['event'] == WalkoffEvent.ConsoleLog:
            action = workflow.get_executing_action()
            sender = action

        event.send(sender, data=kwargs.get('data', None))


class WorkflowResultsReceiver(object):
    def __init__(self, current_app=None):
        """Initialize a Receiver object, which will receive callbacks from the ExecutionElements.

        Args:
            current_app (Flask.App, optional): The current Flask app. If the Receiver is not started separately,
                then the current_app must be included in the init. Otherwise, it should not be included.
            message_converter (WorkflowResultsConverter): Class to convert workflow results
        """
        # TODO: Add figure out better way of doing this import hack
        import api_gateway.server.workflowresults  # Need this import

        self.redis = Redis(host=Config.CACHE["host"], port=Config.CACHE["port"])

        self.workflow_results_pubsub = self.redis.pubsub()
        self.workflow_results_pubsub.subscribe("workflow-results")
        self.action_results_pubsub = self.redis.pubsub()
        self.action_results_pubsub.subscribe("action-results")

        self.thread_exit = False

        self.current_app = current_app

    def receive_results(self):
        """Keep receiving results from execution elements over a ZMQ socket, and trigger the callbacks"""
        while True:
            if self.thread_exit:
                break
            workflow_results_message = self.workflow_results_pubsub.get_message(ignore_subscribe_messages=True)
            if workflow_results_message:
                workflow_results_message = json.loads(workflow_results_message)
                print(workflow_results_message)
                with self.current_app.app_context():
                    self._send_callback(workflow_results_message)

            action_results_message = self.action_results_pubsub.get_message(ignore_subscribe_messages=True)
            if action_results_message:
                action_results_message = json.loads(action_results_message)
                with self.current_app.app_context():
                    self._send_callback(action_results_message.get("data", ''))

            gevent.sleep(0.1)

        return

    def _send_callback(self, message):
        event, sender, data = self._message_to_event_callback(message)

        if sender is not None and event is not None:
            if self.current_app:
                with self.current_app.app_context():
                    event.send(sender, data=data)
            else:
                event.send(sender, data=data)

    def _message_to_event_callback(self, message):
        message = json.loads(message)
        event = WalkoffEvent.get_event_from_name(message.get("status", None))

        if event is not None:
            return event, message, message

        else:
            logger.error(f'Unknown callback {event} sent')
            return None, None, None
