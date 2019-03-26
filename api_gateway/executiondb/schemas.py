from marshmallow import validates_schema, ValidationError, fields, post_dump, post_load, EXCLUDE
from marshmallow.validate import OneOf
from marshmallow_sqlalchemy import ModelSchema, field_for

from api_gateway.executiondb import ExecutionDatabase


# TODO: use these when moving toward storing apis in database
class ExecutionBaseSchema(ModelSchema):
    """Base schema for the execution database.

    This base class adds functionality to strip null fields from serialized objects and attaches the
    execution_db.session on load
    """
    __skipvalues = (None, [], [{}])

    @post_dump
    def _do_post_dump(self, data):
        return self.remove_skip_values(data)

    def remove_skip_values(self, data):
        """Removes fields with empty values from data

        Args:
            data (dict): The data passed in

        Returns:
            (dict): The data with forbidden fields removed
        """
        return {
            key: value for key, value in data.items()
            if value not in self.__skipvalues
        }

    def load(self, data, session=None, instance=None, *args, **kwargs):
        session = ExecutionDatabase.instance.session
        # Maybe automatically find and use instance if 'id' (or key) is passed
        return super(ExecutionBaseSchema, self).load(data, session=session, instance=instance, *args, **kwargs)


class ExecutionElementBaseSchema(ExecutionBaseSchema):
    errors = fields.List(fields.String())
