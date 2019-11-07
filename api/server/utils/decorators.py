from inspect import getfullargspec
from uuid import UUID


def get_id_str(ids):
    return '-'.join([str(id_) for id_ in ids])


def _whitelist_func_kwargs(func, kwargs):
    """ Helper function for decorators that whitelist the wrapped functions kwargs in the case of multiple decorators
        poluting the kwargs.
    """
    func_args = getfullargspec(func).args
    return {key: kwargs[key] for key in func_args}


# def paginate(schema=None):
#     """
#     Paginates the response to a request.
#     Optional schema will schema.dump() the objects returned by the wrapped function
#     """
#
#     def func_wrapper(func):
#         def func_caller(*args, **kwargs):
#             page = request.args.get("page", 1, type=int)
#             start = (page - 1) * current_app.config["ITEMS_PER_PAGE"]
#             stop = start + current_app.config["ITEMS_PER_PAGE"]
#
#             ret, status_code = func(*args, **_whitelist_func_kwargs(func, kwargs))
#             pages = islice(ret, start, stop)
#
#             if schema is not None:
#                 return [schema.dump(obj) for obj in pages], status_code
#
#             return [obj for obj in pages], status_code
#
#         return func_caller
#
#     return func_wrapper


# def validate_resource_exists_factory(resource_name, existence_func):
#     def validate_resource_exists(operation, *ids):
#         def wrapper(func):
#             if existence_func(*ids):
#                 return func
#             else:
#                 return dne_problem(resource_name, operation, ids)
#
#         return wrapper
#
#     return validate_resource_exists
#
#
# def with_resource_factory(resource_name, getter_func, validator=None):
#     """Factory pattern which takes in resource name and resource specific functions, returns a validator decorator"""
#     def arg_wrapper(operation, id_param):
#         """This decorator serves to take in the args to the decorator call and make it available below"""
#         def func_wrapper(func):
#             """This decorator serves to wrap the actual decorated function and return the replacement function below"""
#             def func_caller(*args, **kwargs):
#                 """This decorator is the actual replacement function for the decorated function"""
#                 target_name = kwargs[id_param]
#                 if validator and not validator(target_name):
#                     return invalid_id_problem(resource_name, operation, target_name)
#
#                 # Fetch the resource from the database
#                 # if operation == "update":  # Put/Patch send the object in the body. Dereference id_ from there
#                 #     kwargs[id_param] = getter_func(kwargs["body"]["id_"])
#                 else:
#                     kwargs[id_param] = getter_func(target_name)
#
#                 # Pass the arguments and the dereffed resource to the function
#                 if kwargs[id_param]:
#                     return func(**_whitelist_func_kwargs(func, kwargs))
#                 else:
#                     return dne_problem(resource_name, operation, target_name)
#             return func_caller
#         return func_wrapper
#     return arg_wrapper


def is_valid_uid(*ids):
    try:
        for id_ in ids:
            UUID(id_)
        return True
    except ValueError:
        return False
