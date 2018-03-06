from uuid import UUID

from flask import current_app

from walkoff.server.problem import Problem
from walkoff.server.returncodes import OBJECT_DNE_ERROR, BAD_REQUEST


def get_id_str(ids):
    return '-'.join([str(id_) for id_ in ids])


def resource_not_found_problem(resource, operation, id_):
    return Problem.from_crud_resource(
        OBJECT_DNE_ERROR,
        resource,
        operation,
        '{} {} does not exist.'.format(resource.title(), id_))


def log_operation_error(resource, operation, id_):
    current_app.logger.error('Could not {} {} {}. {} does not exist'.format(operation, resource, id_, resource))


def dne_error(resource, operation, ids):
    id_str = get_id_str(ids)
    log_operation_error(resource, operation, id_str)
    return lambda: (resource_not_found_problem(resource, operation, id_str))


def validate_resource_exists_factory(resource_name, existence_func):
    def validate_resource_exists(operation, *ids):

        def wrapper(func):
            if existence_func(*ids):
                return func
            else:
                return dne_error(resource_name, operation, ids)

        return wrapper

    return validate_resource_exists


def invalid_id_problem(resource, operation):
    return Problem.from_crud_resource(BAD_REQUEST, resource, operation, 'Invalid ID format.')


def with_resource_factory(resource_name, getter_func, validator=None):
    def validate_resource_exists(operation, *ids):
        def wrapper(func):
            if validator and not validator(*ids):
                return lambda: invalid_id_problem(resource_name, operation)

            obj = getter_func(*ids)
            if obj is not None:
                return lambda: func(obj)
            else:
                return dne_error(resource_name, operation, ids)

        return wrapper

    return validate_resource_exists


def is_valid_uid(*ids):
    try:
        for id_ in ids:
            UUID(id_)
        return True
    except ValueError as e:
        return False
