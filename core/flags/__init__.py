from six import with_metaclass
from core.helpers import SubclassRegistry
from connexion.decorators.parameter import get_val_from_param, make_type
__all__ = ['count', 'regMatch']


class FlagExecutionNotImplementedError(NotImplementedError):
    pass


class FlagNotImplementedError(Exception):
    pass


class FlagType(with_metaclass(SubclassRegistry, object)):
    @staticmethod
    def execute(args, value):
        raise FlagExecutionNotImplementedError

import sys, traceback
def execute_flag(action, args=None, value=None):
    from core.helpers import load_flag_function, formatarg
    from core.api import WalkoffAppDefinition
    from core.case.callbacks import FlagArgsInvalid
    if action in FlagType.registry:
        try:
            api = WalkoffAppDefinition(name=action, instance=FlagType.registry[action](), type="flags")
            fn = load_flag_function(api, action)
            try:
                inputs = {}
                # value = get_val_from_param(value, next((param for param in api.operations["execute"].operation["parameters"] if param["name"] == "value"), None))
                format = next((param for param in api.operations["execute"].operation["parameters"] if param["name"] == "value"), None)
                args["value"] = {"key": "value", "format": format, "value": value}
                for input in args:
                    inputs[input] = formatarg(args[input])
                    print(inputs[input])

            except ValueError:
                raise FlagArgsInvalid()

            try:
                response = fn(api=api, action=action, args=inputs)

                print(response.__dict__)
                result = response.body
                if response.status_code == 400:
                    raise Exception
            except Exception as e:
                traceback.print_exception(*sys.exc_info())
                raise Exception

            return result
            #return FlagType.registry[action].execute(args, value)
        except Exception as e:
            print(traceback.print_exception(*sys.exc_info()))
    else:
        raise FlagNotImplementedError
