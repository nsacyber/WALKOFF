import json
import logging

from six import string_types

from walkoff.events import EventType, WalkoffEvent
from walkoff.executiondb.workflow import Workflow
from walkoff.proto.build.data_pb2 import Message

logger = logging.getLogger(__name__)


def convert_to_protobuf(sender, workflow, **kwargs):
    """Converts an execution element and its data to a protobuf message.

    Args:
        sender (execution element): The execution element object that is sending the data.
        workflow (Workflow): The workflow which is sending the event
        kwargs (dict, optional): A dict of extra fields, such as data, callback_name, etc.

    Returns:
        (str): The newly formed protobuf object, serialized as a string to send over the ZMQ socket.
    """
    event = kwargs['event']
    data = kwargs['data'] if 'data' in kwargs else None
    packet = Message()
    packet.event_name = event.name
    if event.event_type == EventType.workflow:
        convert_workflow_to_proto(packet, workflow, data)
    elif event.event_type == EventType.action:
        if event == WalkoffEvent.ConsoleLog:
            convert_log_message_to_protobuf(packet, sender, workflow, **kwargs)
        elif event == WalkoffEvent.SendMessage:
            convert_send_message_to_protobuf(packet, sender, workflow, **kwargs)
        else:
            convert_action_to_proto(packet, sender, workflow, data)
    elif event.event_type in (
            EventType.branch, EventType.condition, EventType.transform, EventType.conditonalexpression):
        convert_branch_transform_condition_to_proto(packet, sender, workflow)
    packet_bytes = packet.SerializeToString()
    return packet_bytes


def convert_workflow_to_proto(packet, sender, data=None):
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
    add_workflow_to_proto(workflow_packet.sender, sender)


def convert_send_message_to_protobuf(packet, message, workflow, **kwargs):
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
    add_workflow_to_proto(message_packet.workflow, workflow)
    if 'users' in kwargs:
        message_packet.users.extend(kwargs['users'])
    if 'roles' in kwargs:
        message_packet.roles.extend(kwargs['roles'])
    if 'requires_reauth' in kwargs:
        message_packet.requires_reauth = kwargs['requires_reauth']


def convert_log_message_to_protobuf(packet, sender, workflow, **kwargs):
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
    add_workflow_to_proto(logging_packet.workflow, workflow)


def convert_action_to_proto(packet, sender, workflow, data=None):
    """Converts an Action to protobuf

    Args:
        packet (protobuf): The protobuf packet
        sender (Action): The Action
        workflow (Workflow): The WOrkflow under which this Action falls
        data (dict, optional): Any additional data. Defaults to None.
    """
    packet.type = Message.ACTIONPACKET
    action_packet = packet.action_packet
    if 'data' is not None:
        action_packet.additional_data = json.dumps(data)
    add_sender_to_action_packet_proto(action_packet, sender)
    add_arguments_to_action_proto(action_packet, sender)
    add_workflow_to_proto(action_packet.workflow, workflow)


def add_sender_to_action_packet_proto(action_packet, sender):
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


def add_arguments_to_action_proto(action_packet, sender):
    """Adds Arguments to the Action protobuf packet

    Args:
        action_packet (protobuf): The protobuf packet
        sender (Action): The Action under which fall the Arguments
    """
    for argument in sender.arguments:
        arg = action_packet.sender.arguments.add()
        arg.name = argument.name
        set_argument_proto(arg, argument)


def set_argument_proto(arg_proto, arg_obj):
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


def add_workflow_to_proto(packet, workflow):
    """Adds a Workflow to a protobuf packet

    Args:
        packet (protobuf): The protobuf packet
        workflow (Workflow): The Workflow object to add to the protobuf message
    """
    packet.name = workflow.name
    packet.id = str(workflow.id)
    packet.execution_id = str(workflow.get_execution_id())


def convert_branch_transform_condition_to_proto(packet, sender, workflow):
    """Converts a Branch, Transform, or Condition to protobuf

    Args:
        packet (protobuf): The protobuf packet
        sender (Branch|Transform|Condition): The object to be converted to protobuf
        workflow (Workflow): The Workflow under which the object falls
    """
    packet.type = Message.GENERALPACKET
    general_packet = packet.general_packet
    general_packet.sender.id = str(sender.id)
    add_workflow_to_proto(general_packet.workflow, workflow)
    if hasattr(sender, 'app_name'):
        general_packet.sender.app_name = sender.app_name
