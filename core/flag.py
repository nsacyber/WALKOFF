from core.executionelement import ExecutionElement
from core.filter import Filter
from core.helpers import (get_flag, get_flag_api, InvalidElementConstructed, InvalidInput,
                          dereference_step_routing, format_exception_message)
from core.validator import validate_flag_parameters, validate_parameter
import logging
import uuid

logger = logging.getLogger(__name__)


class Flag(ExecutionElement):
    def __init__(self, action=None, args=None, filters=None, uid=None):
        """Initializes a new Flag object. 
        
        Args:
            action (str, optional): The action name for the Flag. Defaults to an empty string.
            args (dict[str:str], optional): Dictionary of Argument keys to Argument values. This dictionary will be
                converted to a dictionary of str:Argument. Defaults to None.
            filters(list[Filter], optional): A list of Filter objects for the Flag object. Defaults to None.
            uid (str, optional): A universally unique identifier for this object.
                Created from uuid.uuid4().hex in Python
        """
        self.results_sock = None
        if action is None:
            raise InvalidElementConstructed('Action or xml must be specified in flag constructor')
        ExecutionElement.__init__(self, action, uid)
        self.action = action
        args = args if args is not None else {}
        self.args_api, self.data_in_api = get_flag_api(self.action)
        self.args = validate_flag_parameters(self.args_api, args, self.action)
        self.filters = filters if filters is not None else []

    def send_callback(self, callback_name):
        data = dict()
        data['callback_name'] = callback_name
        data['sender'] = {}
        data['sender']['name'] = self.name
        data['sender']['id'] = self.name
        data['sender']['uid'] = self.uid
        if self.results_sock:
            print("Flag sending {}".format(callback_name))
            import sys
            sys.stdout.flush()
            self.results_sock.send_json(data)

    def __call__(self, data_in, accumulator):
        data = data_in

        for filter_element in self.filters:
            filter_element.results_sock = self.results_sock
            data = filter_element(data, accumulator)
        try:
            data = validate_parameter(data, self.data_in_api, 'Flag {0}'.format(self.action))
            args = dereference_step_routing(self.args, accumulator, 'In Flag {0}'.format(self.name))
            self.send_callback("Flag Success")
            logger.debug('Arguments passed to flag {0} (uid {1}) are valid'.format(self.name, self.uid))
            args.update({self.data_in_api['name']: data})
            return get_flag(self.action)(**args)
        except InvalidInput as e:
            logger.error('Flag {0} has invalid input {1} which was converted to {2}. Error: {3}. '
                         'Returning False'.format(self.action, data_in, data, format_exception_message(e)))
            self.send_callback("Flag Error")
            return False
        except Exception as e:
            logger.error('Error encountered executing '
                         'flag {0} with arguments {1} and value {2}: '
                         'Error {3}. Returning False'.format(self.action, self.args, data, format_exception_message(e)))
            self.send_callback("Flag Error")
            return False

    def as_json(self):
        """Gets the JSON representation of a Flag object.
        
        Returns:
            The JSON representation of a Flag object.
        """
        return {"uid": self.uid,
                "action": self.action,
                "args": [{'name': arg_name, 'value': arg_value} for arg_name, arg_value in self.args.items()],
                "filters": [filter_element.as_json() for filter_element in self.filters]}

    @staticmethod
    def from_json(json_in):
        """Forms a Flag object from the provided JSON object.
        
        Args:
            json_in (JSON object): The JSON object to convert from.
            
        Returns:
            The Flag object parsed from the JSON object.
        """
        args = {arg['name']: arg['value'] for arg in json_in['args']}
        uid = json_in['uid'] if 'uid' in json_in else uuid.uuid4().hex
        filters = [Filter.from_json(filter_element) for filter_element in json_in['filters']]
        flag = Flag(action=json_in['action'], args=args, filters=filters, uid=uid)
        return flag

    def __repr__(self):
        output = {'uid': self.uid,
                  'action': self.action,
                  'args': self.args,
                  'filters': [filter_element.as_json() for filter_element in self.filters]}
        return str(output)
