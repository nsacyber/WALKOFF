import json
import logging

from google.protobuf.json_format import MessageToDict
from six import string_types

from walkoff.events import EventType, WalkoffEvent
from walkoff.executiondb.workflow import Workflow
from walkoff.proto.build.data_pb2 import Message

logger = logging.getLogger(__name__)


class ProtobufWorkflowResultsConverter(object):
    @staticmethod
    def event_to_protobuf(sender, workflow_ctx, **kwargs):
        """Converts an execution element and its data to a protobuf message.

        Args:
            sender (execution element): The execution element object that is sending the data.
            workflow_ctx (WorkflowExecutionContext): The workflow which is sending the event
            kwargs (dict, optional): A dict of extra fields, such as data, callback_name, etc.

        Returns:
            (str): The newly formed protobuf object, serialized as a string to send over the ZMQ socket.
        """
        event = kwargs['event']
        data = kwargs['data'] if 'data' in kwargs else None
        packet = Message()
        packet.event_name = event.name
        if event.event_type == EventType.workflow:
            ProtobufWorkflowResultsConverter._convert_workflow_to_proto(packet, workflow_ctx, data)
        elif event.event_type == EventType.action:
            if event == WalkoffEvent.ConsoleLog:
                ProtobufWorkflowResultsConverter._convert_log_message_to_protobuf(packet, sender, workflow_ctx,
                                                                                  **kwargs)
            elif event == WalkoffEvent.SendMessage:
                ProtobufWorkflowResultsConverter._convert_send_message_to_protobuf(packet, sender, workflow_ctx,
                                                                                   **kwargs)
            else:
                ProtobufWorkflowResultsConverter._convert_action_to_proto(packet, sender, workflow_ctx, data)
        elif event.event_type in (
                EventType.branch, EventType.condition, EventType.transform, EventType.conditonalexpression):
            ProtobufWorkflowResultsConverter._convert_branch_transform_condition_to_proto(packet, sender, workflow_ctx)
        elif event == WalkoffEvent.WorkerReady:
            packet.type = Message.WORKERPACKET
            packet.worker_packet.id = sender['id']
        packet_bytes = packet.SerializeToString()
        return packet_bytes

    @staticmethod
    def _convert_workflow_to_proto(packet, sender, data=None):
        """Converts a Workflow object to a protobuf object

        Args:
            packet (Message): The protobuf packet to add the Workflow to
            sender (Workflow): The Workflow to add to the packet
            data (dict): Any additional data to add to the protobuf packet
        """
        packet.type = Message.WORKFLOWPACKET
        workflow_packet = packet.workflow_packet
        if 'data' is not None:
            workflow_packet.additional_data = json.dumps(data)
        ProtobufWorkflowResultsConverter._add_workflow_to_proto(workflow_packet.sender, sender)

    @staticmethod
    def _convert_send_message_to_protobuf(packet, message, workflow, **kwargs):
        """Converts a Message object to a protobuf object

        Args:
            packet (protobuf): The protobuf packet
            message (Message): The Message object to be converted
            workflow (Workflow): The Workflow relating to this Message
            **kwargs (dict, optional): Any additional arguments
        """
        packet.type = Message.USERMESSAGE
        message_packet = packet.message_packet
        message_packet.subject = message.pop('subject', '')
        message_packet.body = json.dumps(message['body'])
        ProtobufWorkflowResultsConverter._add_workflow_to_proto(message_packet.workflow, workflow)
        if 'users' in kwargs:
            message_packet.users.extend(kwargs['users'])
        if 'roles' in kwargs:
            message_packet.roles.extend(kwargs['roles'])
        if 'requires_reauth' in kwargs:
            message_packet.requires_reauth = kwargs['requires_reauth']

    @staticmethod
    def _convert_log_message_to_protobuf(packet, sender, workflow, **kwargs):
        """Converts a logging message to protobuf

        Args:
            packet (protobuf): The protobuf packet
            sender (Action): The Action from which this logging message originated
            workflow (Workflow): The Workflow under which this Action falls
            **kwargs (dict, optional): Any additional arguments
        """
        packet.type = Message.LOGMESSAGE
        logging_packet = packet.logging_packet
        logging_packet.name = sender.name
        logging_packet.app_name = sender.app_name
        logging_packet.action_name = sender.action_name
        logging_packet.level = str(kwargs['level'])  # Needed just in case logging level is set to an int
        logging_packet.message = kwargs['message']
        ProtobufWorkflowResultsConverter._add_workflow_to_proto(logging_packet.workflow, workflow)

    @staticmethod
    def _convert_action_to_proto(packet, sender, workflow_ctx, data=None):
        """Converts an Action to protobuf

        Args:
            packet (protobuf): The protobuf packet
            sender (Action): The Action
            workflow_ctx (WorkflowExecutionContext): The Workflow under which this Action falls
            data (dict, optional): Any additional data. Defaults to None.
        """
        packet.type = Message.ACTIONPACKET
        action_packet = packet.action_packet

        arguments = None
        if data is not None:
            arguments = data.pop('start_arguments', None)
            action_packet.additional_data = json.dumps(data)

        ProtobufWorkflowResultsConverter._add_sender_to_action_packet_proto(action_packet, sender)

        arguments = arguments if arguments else sender.arguments
        if arguments:
            ProtobufWorkflowResultsConverter._add_arguments_to_action_proto(action_packet, arguments)

        ProtobufWorkflowResultsConverter._add_workflow_to_proto(action_packet.workflow, workflow_ctx)

    @staticmethod
    def _add_sender_to_action_packet_proto(action_packet, sender):
        """Adds a sender to a protobuf packet

        Args:
            action_packet (protobuf): The protobuf packet
            sender (Action): The sender
        """
        action_packet.sender.name = sender.name
        action_packet.sender.id = str(sender.id)
        action_packet.sender.execution_id = sender.get_execution_id()
        action_packet.sender.app_name = sender.app_name
        action_packet.sender.action_name = sender.action_name
        action_packet.sender.device_id = sender.get_resolved_device_id()

    @staticmethod
    def _add_arguments_to_action_proto(action_packet, arguments):
        """Adds Arguments to the Action protobuf packet

        Args:
            action_packet (protobuf): The protobuf packet
            arguments (list[Argument]): The list of Arguments to add
        """
        for argument in arguments:
            arg = action_packet.sender.arguments.add()
            arg.name = argument.name
            ProtobufWorkflowResultsConverter._set_argument_proto(arg, argument)

    @staticmethod
    def _set_argument_proto(arg_proto, arg_obj):
        """Sets up the Argument protobuf

        Args:
            arg_proto (protobuf): The Argument protobuf field
            arg_obj (Argument): The Argument object
        """
        arg_proto.name = arg_obj.name
        for field in ('value', 'reference', 'selection'):
            val = getattr(arg_obj, field)
            if val is not None:
                if not isinstance(val, string_types):
                    try:
                        setattr(arg_proto, field, json.dumps(val))
                    except (ValueError, TypeError):
                        setattr(arg_proto, field, str(val))
                else:
                    setattr(arg_proto, field, val)

    @staticmethod
    def add_env_vars_to_proto(packet, env_vars):
        """Sets up the EnvironmentVariable protobuf

        Args:
            packet (protobuf): The protobuf field
            env_vars (list[EnvironmentVariable]): The EnvironmentVariables to add to the protobuf object
        """
        for env_var in env_vars:
            ev_proto = packet.environment_variables.add()
            ev_proto.id = str(env_var.id)
            ev_proto.value = env_var.value

    @staticmethod
    def _add_workflow_to_proto(packet, workflow):
        """Adds a Workflow to a protobuf packet

        Args:
            packet (protobuf): The protobuf packet
            workflow (Workflow): The Workflow object to add to the protobuf message
        """
        packet.name = workflow.name
        packet.id = str(workflow.id)
        packet.execution_id = str(workflow.get_execution_id())

    @staticmethod
    def _convert_branch_transform_condition_to_proto(packet, sender, workflow):
        """Converts a Branch, Transform, or Condition to protobuf

        Args:
            packet (protobuf): The protobuf packet
            sender (Branch|Transform|Condition): The object to be converted to protobuf
            workflow (Workflow): The Workflow under which the object falls
        """
        packet.type = Message.GENERALPACKET
        general_packet = packet.general_packet
        general_packet.sender.id = str(sender.id)
        ProtobufWorkflowResultsConverter._add_workflow_to_proto(general_packet.workflow, workflow)
        if hasattr(sender, 'app_name'):
            general_packet.sender.app_name = sender.app_name

    @staticmethod
    def to_event_callback(message_bytes):

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
        event = WalkoffEvent.get_event_from_name(callback_name)
        if event is not None:
            data = ProtobufWorkflowResultsConverter._format_callback_data(event, message)
            return sender, data
        else:
            logger.error('Unknown callback {} sent'.format(callback_name))
            return None, None

    @staticmethod
    def _format_callback_data(event, message):
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
                data['message'] = ProtobufWorkflowResultsConverter.format_message_event_data(message)
        return data

    @staticmethod
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
