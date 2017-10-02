from core.executionelement import ExecutionElement
from core.filter import Filter
from core.helpers import (get_flag, get_flag_api, InvalidElementConstructed, InvalidInput,
                          dereference_step_routing, format_exception_message)
from core.validator import validate_flag_parameters, validate_parameter
from core.case.callbacks import data_sent
import logging

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
        if action is None:
            raise InvalidElementConstructed('Action or xml must be specified in flag constructor')
        ExecutionElement.__init__(self, uid)
        self.action = action
        args = args if args is not None else {}
        self._args_api, self._data_in_api = get_flag_api(self.action)
        self.args = validate_flag_parameters(self._args_api, args, self.action)
        self.filters = filters if filters is not None else []

    def __send_callback(self, callback_name):
        data = dict()
        data['callback_name'] = callback_name
        data['sender'] = {}
        data['sender']['uid'] = self.uid
        data_sent.send(None, data=data)

    def __call__(self, data_in, accumulator):
        data = data_in

        for filter_element in self.filters:
            data = filter_element(data, accumulator)
        try:
            data = validate_parameter(data, self._data_in_api, 'Flag {0}'.format(self.action))
            args = dereference_step_routing(self.args, accumulator, 'In Flag {0}'.format(self.uid))
            self.__send_callback("Flag Success")
            logger.debug('Arguments passed to flag {} are valid'.format(self.uid))
            args.update({self._data_in_api['name']: data})
            return get_flag(self.action)(**args)
        except InvalidInput as e:
            logger.error('Flag {0} has invalid input {1} which was converted to {2}. Error: {3}. '
                         'Returning False'.format(self.action, data_in, data, format_exception_message(e)))
            self.__send_callback("Flag Error")
            return False
        except Exception as e:
            logger.error('Error encountered executing '
                         'flag {0} with arguments {1} and value {2}: '
                         'Error {3}. Returning False'.format(self.action, self.args, data, format_exception_message(e)))
            self.__send_callback("Flag Error")
            return False

    @staticmethod
    def from_json(json_in):
        """Forms a Flag object from the provided JSON object.
        
        Args:
            json_in (JSON object): The JSON object to convert from.
            
        Returns:
            The Flag object parsed from the JSON object.
        """
        args = {arg['name']: arg['value'] for arg in json_in['args']}
        uid = json_in['uid'] if 'uid' in json_in else None
        filters = [Filter.from_json(filter_element) for filter_element in json_in['filters']]
        flag = Flag(action=json_in['action'], args=args, filters=filters, uid=uid)
        return flag

    def __repr__(self):
        output = {'uid': self.uid,
                  'action': self.action,
                  'args': self.args,
                  'filters': [filter_element.read() for filter_element in self.filters]}
        return str(output)
