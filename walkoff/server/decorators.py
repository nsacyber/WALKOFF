from flask import current_app
from walkoff.server.returncodes import OBJECT_DNE_ERROR


def validate_resource_exists_factory(resource_name, existence_func):

    resource_dne_message = '{} does not exist'.format(resource_name.title())

    def validate_resource_exists(operation, *ids):

        def wrapper(func):
            if existence_func(*ids):
                return func
            else:
                current_app.logger.error(
                    'Could not {0} {1} {2}. {3}'.format(
                        operation, resource_name, '-'.join([str(id_) for id_ in ids]), resource_dne_message)
                )
                return lambda: ({'error': resource_dne_message}, OBJECT_DNE_ERROR)
        return wrapper

    return validate_resource_exists


def with_resource_factory(resource_name, getter_func):

    resource_dne_message = '{} does not exist'.format(resource_name.title())

    def validate_resource_exists(operation, *ids):

        def wrapper(func):
            obj = getter_func(*ids)
            if obj is not None:
                return lambda: func(obj)
            else:
                current_app.logger.error(
                    'Could not {0} {1} {2}. {3}'.format(
                        operation, resource_name, '-'.join([str(id_) for id_ in ids]), resource_dne_message)
                )
                return lambda: ({'error': resource_dne_message}, OBJECT_DNE_ERROR)
        return wrapper

    return validate_resource_exists
