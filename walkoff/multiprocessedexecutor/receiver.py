import json
import logging
import os

import gevent
import zmq.auth as auth
import zmq.green as zmq
from google.protobuf.json_format import MessageToDict

import walkoff.config
from walkoff.events import WalkoffEvent, EventType
from walkoff.proto.build.data_pb2 import Message
from flask import Flask
from walkoff.server import context

logger = logging.getLogger(__name__)


class Receiver:
    def __init__(self, current_app=None):
        """Initialize a Receiver object, which will receive callbacks from the ExecutionElements.

        Args:
            current_app (Flask.App, optional): The current Flask app. If the Receiver is not started separately,
                then the current_app must be included in the init. Otherwise, it should not be included.
        """
        ctx = zmq.Context.instance()
        self.thread_exit = False
        self.workflows_executed = 0

        server_secret_file = os.path.join(walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH, "server.key_secret")
        server_public, server_secret = auth.load_certificate(server_secret_file)

        self.results_sock = ctx.socket(zmq.PULL)
        self.results_sock.curve_secretkey = server_secret
        self.results_sock.curve_publickey = server_public
        self.results_sock.curve_server = True
        self.results_sock.bind(walkoff.config.Config.ZMQ_RESULTS_ADDRESS)

        if current_app is None:
            from walkoff.server import workflowresults  # This import must stay
            self.current_app = Flask(__name__)
            self.current_app.config.from_object(walkoff.config.Config)
            self.current_app.running_context = context.Context(walkoff.config.Config, init_all=False)
        else:
            self.current_app = current_app

    def receive_results(self):
        """Keep receiving results from execution elements over a ZMQ socket, and trigger the callbacks"""
        print("Receiver started and awaiting results")
        while True:
            if self.thread_exit:
                break
            try:
                message_bytes = self.results_sock.recv(zmq.NOBLOCK)
            except zmq.ZMQError:
                gevent.sleep(0.1)
                continue

            with self.current_app.app_context():
                self._send_callback(message_bytes)

        self.results_sock.close()
        return

    def _send_callback(self, message_bytes):

        message_outer = Message()
        message_outer.ParseFromString(message_bytes)
        callback_name = message_outer.event_name

        if message_outer.type == Message.WORKFLOWPACKET:
            message = message_outer.workflow_packet
        elif message_outer.type == Message.ACTIONPACKET:
            message = message_outer.action_packet
        elif message_outer.type == Message.USERMESSAGE:
            message = message_outer.message_packet
        elif message_outer.type == Message.LOGMESSAGE:
            message = message_outer.logging_packet
        else:
            message = message_outer.general_packet

        if hasattr(message, "sender"):
            sender = MessageToDict(message.sender, preserving_proto_field_name=True)
        elif hasattr(message, "workflow"):
            sender = MessageToDict(message.workflow, preserving_proto_field_name=True)
        print(callback_name)
        event = WalkoffEvent.get_event_from_name(callback_name)
        if event is not None:
            data = self._format_data(event, message)
            if self.current_app:
                with self.current_app.app_context():
                    event.send(sender, data=data)
            else:
                event.send(sender, data=data)
            if event in [WalkoffEvent.WorkflowShutdown, WalkoffEvent.WorkflowAborted]:
                self._increment_execution_count()
        else:
            logger.error('Unknown callback {} sent'.format(callback_name))

    @staticmethod
    def _format_data(event, message):
        if event == WalkoffEvent.ConsoleLog:
            data = MessageToDict(message, preserving_proto_field_name=True)
        elif event.event_type != EventType.workflow:
            data = {'workflow': MessageToDict(message.workflow, preserving_proto_field_name=True)}
        else:
            data = {}
        if event.requires_data():
            if event != WalkoffEvent.SendMessage:
                data['data'] = json.loads(message.additional_data)
            else:
                data['message'] = format_message_event_data(message)
        return data

    def _increment_execution_count(self):
        self.workflows_executed += 1


def format_message_event_data(message):
    """Formats a Message

    Args:
        message (Message): The Message to be formatted

    Returns:
        (dict): The formatted Message object
    """
    return {'users': message.users,
            'roles': message.roles,
            'requires_reauth': message.requires_reauth,
            'body': json.loads(message.body),
            'subject': message.subject}
