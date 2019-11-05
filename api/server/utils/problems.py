import logging
from http import HTTPStatus

from fastapi.exceptions import HTTPException
from starlette.responses import JSONResponse

logger = logging.getLogger("API")


class ProblemException(HTTPException):
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
        # response = Problem.make_response_body(status, title, detail, instance, type_, ext)
        super().__init__(status_code=status, detail=detail, headers=headers)
        self.title = title
        self.instance = instance
        self.type = type_ if type_ else "about:blank"
        self.ext = ext if ext is not None else {}

    def as_dict(self):
        r = {
            "title": self.title,
            "instance": self.instance,
            "type": self.type,
            "detail": self.detail,
            "status": self.status_code
        }
        r.update(self.ext)
        return r

    def as_response(self):
        return JSONResponse(self.as_dict(), status_code=self.status_code)

    #
    # @staticmethod
    # def make_response_body(status, title, detail, instance=None, type_=None, ext=None):
    #     if not type_:
    #         type_ = "about:blank"
    #
    #     response = {"type": type_, "title": title, "detail": detail, "status": status}
    #     if instance:
    #         response["instance"] = instance
    #     if ext:
    #         response.update(ext)
    #
    #     return response
    #
    # @classmethod
    # def from_crud_resource(cls, status, resource, operation, detail, instance=None, type_=None, ext=None, headers=None):
    #     title = f"Could not {operation} {resource}."
    #     return cls(status, title, detail, instance=instance, type_=type_, ext=ext, headers=headers)


class UnauthorizedException(ProblemException):
    def __init__(self, operation, resource, id_):
        detail = f"Could not {operation} {resource} {id_}, user is unauthorized to perform this action."
        super().__init__(HTTPStatus.FORBIDDEN, "Unauthorized", detail=detail)


class UniquenessException(ProblemException):
    def __init__(self, operation, resource, id_):
        detail = f"Could not {operation} {resource} {id_}, another object with this name or ID already exists."
        super().__init__(HTTPStatus.BAD_REQUEST, "Uniqueness Constraint Failed", detail=detail)


class ImproperJSONException(ProblemException):
    def __init__(self, operation, resource, id_, errors=None):
        detail = f"Could not {operation} {resource} {id_}, invalid JSON."
        super().__init__(HTTPStatus.BAD_REQUEST, "Improper JSON", detail=detail, ext={"errors": errors})


class InvalidInputException(ProblemException):
    def __init__(self, operation, resource, id_, errors=None):
        detail = f"Could not {operation} {resource} {id_}, invalid input."
        super().__init__(HTTPStatus.BAD_REQUEST, "Invalid Input", detail=detail, ext={"errors": errors})


class InvalidIDException(ProblemException):
    def __init__(self, operation, resource, id_):
        detail = f"Could not {operation} {resource} {id_}, invalid ID."
        super().__init__(HTTPStatus.BAD_REQUEST, "Invalid ID", detail=detail)


class DoesNotExistException(ProblemException):
    def __init__(self, operation, resource, id_):
        detail = f"Could not {operation} {resource} {id_}, does not exist."
        super().__init__(HTTPStatus.NOT_FOUND, f"{resource} does not exist", detail=detail)


# def unique_constraint_problem(resource, operation, id_):
#     detail = f"Could not {operation} {resource} {id_}, possibly because of invalid or non-unique IDs"
#     logger.error(detail)
#     return Problem.from_crud_resource(HTTPStatus.BAD_REQUEST, resource, operation, detail)
#
#
# def improper_json_problem(resource, operation, id_, errors=None):
#     detail = f"Could not {operation} {resource} {id_}. Invalid JSON"
#     logger.error(f"{detail}. Details: {errors}")
#     return Problem.from_crud_resource(HTTPStatus.BAD_REQUEST, resource, operation, detail, ext={"errors": errors})
#
#
# def invalid_input_problem(resource, operation, id_, errors=None):
#     detail = f"Could not {operation} {resource} {id_}. Invalid input"
#     logger.error(f"{detail}. Details: {errors}")
#     return Problem.from_crud_resource(HTTPStatus.BAD_REQUEST, resource, operation, detail, ext={"errors": errors})
#
#
# def invalid_id_problem(resource, operation, id_):
#     detail = f"Could not {operation} {resource}. {id_} is an invalid ID"
#     logger.error(detail)
#     return Problem.from_crud_resource(HTTPStatus.BAD_REQUEST, resource, operation, detail)
#
#
# def dne_problem(resource, operation, id_, errors=None):
#     detail = f"Could not {operation} {resource} {id_}. {resource.title()} does not exist"
#     logger.error(f"{detail}. Details: {errors}")
#     return Problem.from_crud_resource(HTTPStatus.NOT_FOUND, resource, operation, detail, ext=errors)
