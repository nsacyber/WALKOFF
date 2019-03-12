import json
import logging
import os.path

import api_gateway.config
from api_gateway.appgateway.apiutil import UnknownApp, UnknownAppAction, InvalidParameter, UnknownCondition, UnknownTransform
from api_gateway.executiondb.schemas import WorkflowSchema
from api_gateway.helpers import format_exception_message

logger = logging.getLogger(__name__)


def load_workflow(resource, workflow_name):
    """Loads a workflow from a file.

    Args:
        resource (str): Path to the workflow.
        workflow_name (str): Name of the workflow to load.

    Returns:
        True on success, False otherwise.
    """
    try:
        with open(resource, 'r') as workflow_file:
            workflow_string = workflow_file.read()
            try:
                workflow_json = json.loads(workflow_string)
                workflow_name = workflow_json['name']
                workflow = WorkflowSchema().load(workflow_json)
                return workflow_name, workflow
            except ValueError as e:
                logger.exception(f"Could not parse {resource}: {format_exception_message(e)}")
                return None
            except (InvalidParameter, UnknownApp, UnknownAppAction, UnknownTransform, UnknownCondition) as e:
                logger.error(f"Could not validate {workflow_name}: {format_exception_message(e)}")
                return None
    except (IOError, OSError) as e:
        logger.error(f"Could not load {resource}: {format_exception_message(e)}")
        return None

    # @staticmethod
    # def load_playbook(resource):
    #     """Loads a playbook from a file.
    #
    #     Args:
    #         resource (str): Path to the workflow.
    #     """
    #     try:
    #         playbook_file = open(resource, 'r')
    #     except (IOError, OSError) as e:
    #         logger.error('Could not load workflow from {0}. Reason: {1}'.format(resource, format_exception_message(e)))
    #         return None
    #     else:
    #         with playbook_file:
    #             workflow_loaded = playbook_file.read()
    #             try:
    #                 playbook_json = json.loads(workflow_loaded)
    #
    #                 playbook = PlaybookSchema().load(playbook_json)
    #                 return playbook
    #             except ValueError as e:
    #                 logger.exception('Cannot parse {0}. Reason: {1}'.format(resource, format_exception_message(e)))
    #             except (InvalidParameter, UnknownApp, UnknownAppAction, UnknownTransform, UnknownCondition) as e:
    #                 logger.error(
    #                     'Error constructing playbook from {0}. '
    #                     'Reason: {1}'.format(resource, format_exception_message(e)))
    #                 return None
    #
    # @staticmethod
    # def load_playbooks(resource_collection=None):
    #     """Loads all playbooks from a directory.
    #
    #     Args:
    #         resource_collection (str, optional): Path to the directory to load from. Defaults to the configuration
    #             workflows_path.
    #     """
    #
    #     if resource_collection is None:
    #         resource_collection = api_gateway.config.Config.WORKFLOWS_PATH
    #     playbooks = [JsonPlaybookLoader.load_playbook(os.path.join(resource_collection, playbook))
    #                  for playbook in locate_playbooks_in_directory(resource_collection)]
    #     return [playbook for playbook in playbooks if playbook]
