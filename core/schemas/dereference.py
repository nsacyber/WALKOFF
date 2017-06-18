import logging
from core.validator import InvalidApi

logger = logging.getLogger(__name__)


# TODO: jsonschema library has a more evolved dereferencer which can use http and files. We should use that.
def dereference(reference, spec, seen, message_prefix):
    if reference in seen:
        raise InvalidApi(
            '{0}: Improper reference path "{1}". Circular reference detected'.format(message_prefix, reference))
    seen.add(reference)
    reference_path = reference.split('/')
    if not reference_path or not reference_path[0] == '#' or len(reference_path) == 1:
        raise InvalidApi(
            '{0}: Improperly formatted reference path "{1}". '
            'Proper format is "#/path/to/reference.'.format(message_prefix, reference))
    working_schema = spec
    for path_element in reference_path[1:]:
        try:
            working_schema = working_schema[path_element]
        except KeyError:
            raise InvalidApi(
                '{0}: Improper reference path "{1}". '
                'Path element "{2}" not found'.format(message_prefix, reference, path_element))
    return working_schema


def __flatted_dict(schema, spec, path, message_prefix, seen):
    accumulator = {}
    for schema_element_name, schema_element in schema.items():
        if schema_element_name == '$ref':
            dereferenced = dereference(schema_element, spec, seen, message_prefix)
            flatten(dereferenced, spec, message_prefix, path=path, seen=seen)
        else:
            new_path = path.append(schema_element_name)
            accumulator[schema_element_name] = flatten(schema_element, spec, message_prefix, path=new_path, seen=seen)
    swap_for_flattened(spec, path, accumulator)
    return accumulator


def __flatted_list(schema, spec, path, message_prefix, seen):
    accumulator = []
    for schema_element in schema:
        accumulator.append(flatten(schema_element, spec, message_prefix, path=path, seen=seen))
    return accumulator


def swap_for_flattened(spec, path, flattened):
    """
    In place swap of an element of the spec specified by the path with the flattened element
    """
    parent = None
    working = spec
    for path_element in path:
        parent = working
        working = working[path_element]
    parent[path_element] = flattened  # IDE says variable referenced before assignment. It's lying.


def flatten(spec, message_prefix, schema=None, path=None, seen=None):
    seen = seen if seen is not None else set()
    path = path if path is not None else []
    schema = schema if schema is not None else spec
    if isinstance(schema, dict):
        __flatted_dict(schema, spec, path, message_prefix, seen)
    elif isinstance(schema, list):
        __flatted_list(schema, spec, path, message_prefix, seen)
    else:
        return schema


def flatten_spec(spec, message_prefix):
    for spec_element_name, spec_element in spec.items():
        message_prefix = '{0} [{1}]'.format(message_prefix, spec_element_name)
        spec[spec_element_name] = flatten(spec_element, spec, message_prefix)

# def __flatted_dict(schema, spec, message_prefix, seen):
#     accumulator = {}
#     for schema_element_name, schema_element in schema.items():
#         if schema_element_name == '$ref':
#             dereferenced = dereference(schema_element, spec, seen, message_prefix)
#             return flatten(dereferenced, spec, message_prefix, seen)
#         else:
#             accumulator[schema_element_name] = flatten(schema_element, spec, message_prefix, seen)
#     return accumulator
#
#
# def __flatted_list(schema, spec, message_prefix, seen):
#     accumulator = []
#     for schema_element in schema:
#         accumulator.append(flatten(schema_element, spec, message_prefix, seen))
#     return accumulator
#
#
# def flatten(schema, spec, message_prefix, seen=None):
#     seen = seen if seen is not None else set()
#     if isinstance(schema, dict):
#         return __flatted_dict(schema, spec, message_prefix, seen)
#     elif isinstance(schema, list):
#         return __flatted_list(schema, spec, message_prefix, seen)
#     else:
#         return schema
#
#
# def flatten_spec(spec, message_prefix):
#     for spec_element_name, spec_element in spec.items():
#         message_prefix = '{0} [{1}]'.format(message_prefix, spec_element_name)
#         spec[spec_element_name] = flatten(spec_element, spec, message_prefix)