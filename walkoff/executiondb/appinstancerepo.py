import logging

from walkoff.appgateway.appinstance import AppInstance
from walkoff.events import WalkoffEvent
from walkoff.helpers import format_exception_message

logger = logging.getLogger(__name__)


class AppInstanceRepo(object):
    def __init__(self, instances=None):
        self._instances = {}
        if instances:
            self._instances = instances

    def setup_app_instance(self, action, accumulator):
        device_id = (action.app_name, action.device_id.get_value(accumulator))
        if device_id not in self._instances:
            self._instances[device_id] = AppInstance.create(action.app_name, action.device_id)
            WalkoffEvent.CommonWorkflowSignal.send(self, event=WalkoffEvent.AppInstanceCreated)
            logger.debug('Created new app instance: App {0}, device {1}'.format(action.app_name, action.device_id))
        return device_id

    def get_app_instance(self, device_id):
        if device_id in self._instances:
            return self._instances[device_id]
        return None

    def get_all_app_instances(self):
        return self._instances

    def set_all_app_instances(self, instances):
        self._instances = instances

    def shutdown_instances(self):
        for instance_name, instance in self._instances.items():
            try:
                if instance() is not None:
                    logger.debug('Shutting down app instance: Device: {0}'.format(instance_name))
                    instance.shutdown()
            except Exception as e:
                logger.error('Error caught while shutting down app instance. '
                             'Device: {0}. Error {1}'.format(instance_name, format_exception_message(e)))
