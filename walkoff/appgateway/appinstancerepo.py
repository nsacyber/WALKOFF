import logging

from walkoff.appgateway.appinstance import AppInstance
from walkoff.events import WalkoffEvent
from walkoff.helpers import format_exception_message

logger = logging.getLogger(__name__)


class AppInstanceRepo(object):
    """A repository of AppInstance objects

    Attributes:
        _instances (dict): The in-memory repository of AppInstance objects

    Args:
        instances (dict{tuple(app_name, device_id): AppInstance}, optional): An existing repository of device ID to
            AppInstance to initialize this repository to.
    """

    def __init__(self, instances=None):
        self._instances = instances or {}

    def setup_app_instance(self, action, workflow_ctx):
        """Sets up an AppInstance for a device in an action

        Args:
            action (Action): The Action which has the Device
            workflow_ctx (WorkflowExecutionContext): The Workflow which has the Action

        Returns:
            (tuple(app_name, device_id)): A tuple containing the app name for the Action, and the device_id int
        """
        if action.device_id:
            device_id = (action.app_name, action.device_id.get_value(workflow_ctx.accumulator))
            if device_id not in self._instances:
                self._instances[device_id] = AppInstance.create(*device_id)
                WalkoffEvent.CommonWorkflowSignal.send(workflow_ctx.workflow, event=WalkoffEvent.AppInstanceCreated)
                logger.debug('Created new app instance: App {0}, device {1}'.format(*device_id))
            return device_id
        return None

    def get_app_instance(self, device_id):
        """Gets the AppInstance given a device ID

        Args:
            device_id (tuple(app_name, device_id)): The device_id tuple containing the app name and the device_id

        Returns:
            (AppInstance): The AppInstance for the given device_id tuple. Setup_app_instance() must have been called
                before this function is called
        """
        return self._instances.get(device_id, None)

    def get_all_app_instances(self):
        """Gets all AppInstance objects

        Returns:
            dict(dict{tuple(app_name, device_id): AppInstance}): A dictionary containing all of the AppInstance objs
        """
        return self._instances

    def set_all_app_instances(self, instances):
        """Sets the AppInstance attribute

        Args:
            instances (dict{tuple(app_name, device_id): AppInstance}): A dict containing the new AppInstance objs

        Returns:

        """
        self._instances = instances

    def shutdown_instances(self):
        """Calls the shutdown() method on all of the AppInstance objects"""
        for instance_name, instance in self._instances.items():
            try:
                if instance() is not None:
                    logger.debug('Shutting down app instance: Device: {0}'.format(instance_name))
                    instance.shutdown()
            except Exception as e:
                logger.exception('Error caught while shutting down app instance. '
                                 'Device: {0}. Error {1}'.format(instance_name, format_exception_message(e)))
