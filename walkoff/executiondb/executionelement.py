from sqlalchemy_utils import UUIDType

from walkoff.executiondb.representable import Representable
from sqlalchemy import Column
from uuid import uuid4


class ExecutionElement(Representable):
    id = Column(UUIDType(), primary_key=True, nullable=False, default=uuid4)

    def __init__(self, id):
        if id:
            self.id = id

    # def regenerate_ids(self, with_children=True, action_mapping=None):
    #     """
    #     Regenerates the IDs of the execution element and its children
    #     Args:
    #         with_children (bool optional): Regenerate the childrens' IDs of this object? Defaults to True
    #         action_mapping (dict, optional): The dictionary of prev action IDs to new action IDs. Defaults to None.
    #     """
    #     self.id = str(uuid4())
    #
    #     if hasattr(self, 'reference') and self.reference is not None:
    #         self.reference = action_mapping[self.reference]
    #
    #     if with_children:
    #         for field, value in ((field, getattr(self, field)) for field in dir(self)
    #                              if not callable(getattr(self, field))):
    #             if isinstance(value, list):
    #                 self.__regenerate_ids_of_list(value, action_mapping)
    #             elif isinstance(value, dict):
    #                 self.__regenerate_ids_of_dict(value, action_mapping)
    #             elif isinstance(value, ExecutionElement):
    #                 value.regenerate_ids(action_mapping=action_mapping)
    #
    # @staticmethod
    # def __regenerate_ids_of_dict(value, action_mapping=None):
    #     for dict_element in (element for element in value.values() if
    #                          isinstance(element, ExecutionElement)):
    #         dict_element.regenerate_ids(action_mapping=action_mapping)
    #
    # @staticmethod
    # def __regenerate_ids_of_list(value, action_mapping):
    #     for list_element in (list_element_ for list_element_ in value
    #                          if isinstance(list_element_, ExecutionElement)):
    #         list_element.regenerate_ids(action_mapping=action_mapping)

    def __repr__(self):
        representation = self.read()
        out = '<{0} at {1} : '.format(self.__class__.__name__, hex(id(self)))
        first = True
        for key, value in representation.items():
            if self.__is_list_of_dicts_with_uids(value):
                out += ', {0}={1}'.format(key, [list_value['uid'] for list_value in value])
            else:
                out += ', {0}={1}'.format(key, value)

            if first:
                out = out.replace(" ,", "")
                first = False

        out += '>'
        return out

    @staticmethod
    def __is_list_of_dicts_with_uids(value):
        return (isinstance(value, list)
                and all(isinstance(list_value, dict) and 'uid' in list_value for list_value in value))
