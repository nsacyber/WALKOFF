import json
import logging

from starlette.responses import JSONResponse

from http import HTTPStatus

logger = logging.getLogger("API")


class Problem(JSONResponse):
    """Returns a Problem Details object complying with RFC 7807
    .. https://tools.ietf.org/html/rfc7807

    Args:
        status (int): The HTTP status code generated for this occurrence of the problem
        title (str): A short, human-readable summary of the problem type. It SHOULD NOT change from occurrence to
            occurrence of the problem, except for purposes of localization
        detail (str): A human-readable explanation specific to this occurrence of the problem
        instance (str, optional): A URI reference that identifies the specific occurrence of the problem. It may or may
            not yield further information if dereferenced.
        type_ (str, optional): A URI reference that identifies the problem type. When dereferenced it should provide
            human-readable documentation for the problem type. Defaults to 'about:blank'
        ext (dict, optional): Other information to attach to the problem
        headers (dict, optional): Headers to use for this response

    """

    def __init__(self, status, title, detail, instance=None, type_=None, ext=None, headers=None):
        response = Problem.make_response_body(status, title, detail, instance, type_, ext)
        JSONResponse.__init__(self, content=response, status_code=status, headers=headers)

    @staticmethod
    def make_response_body(status, title, detail, instance=None, type_=None, ext=None):
        if not type_:
            type_ = "about:blank"

        response = {"type": type_, "title": title, "detail": detail, "status": status}
        if instance:
            response["instance"] = instance
        if ext:
            response.update(ext)

        return json.dumps(response)

    @classmethod
    def from_crud_resource(cls, status, resource, operation, detail, instance=None, type_=None, ext=None, headers=None):
        title = f"Could not {operation} {resource}."
        return cls(status, title, detail, instance=instance, type_=type_, ext=ext, headers=headers)


def unique_constraint_problem(resource, operation, id_):
    detail = f"Could not {operation} {resource} {id_}, possibly because of invalid or non-unique IDs"
    logger.error(detail)
    return Problem.from_crud_resource(HTTPStatus.BAD_REQUEST, resource, operation, detail)


def improper_json_problem(resource, operation, id_, errors=None):
    detail = f"Could not {operation} {resource} {id_}. Invalid JSON"
    logger.error(f"{detail}. Details: {errors}")
    return Problem.from_crud_resource(HTTPStatus.BAD_REQUEST, resource, operation, detail, ext={"errors": errors})


def invalid_input_problem(resource, operation, id_, errors=None):
    detail = f"Could not {operation} {resource} {id_}. Invalid input"
    logger.error(f"{detail}. Details: {errors}")
    return Problem.from_crud_resource(HTTPStatus.BAD_REQUEST, resource, operation, detail, ext={"errors": errors})


def invalid_id_problem(resource, operation, id_):
    detail = f"Could not {operation} {resource}. {id_} is an invalid ID"
    logger.error(detail)
    return Problem.from_crud_resource(HTTPStatus.BAD_REQUEST, resource, operation, detail)


def dne_problem(resource, operation, id_, errors=None):
    detail = f"Could not {operation} {resource} {id_}. {resource.title()} does not exist"
    logger.error(f"{detail}. Details: {errors}")
    return Problem.from_crud_resource(HTTPStatus.NOT_FOUND, resource, operation, detail, ext=errors)
