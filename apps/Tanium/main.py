from core import app
import json
import os
import sys
import tempfile
import pprint
import traceback


#There is an associated Hello world test workflow which can be executed

class Main(app.App):
    def __init__(self, name=None, device=None):
        app.App.__init__(self, name, device)
        self.introMessage = "I SAY THIS BEFORE EVERY FUNCTION: HELLO WORLD"


        sys.dont_write_bytecode = True

        pytan_loc = "./apps/Tanium"

        pytan_static_path = os.path.join(pytan_loc, 'lib')

        my_file = os.path.abspath(sys.argv[0])
        my_dir = os.path.dirname(my_file)

        parent_dir = os.path.dirname(my_dir)
        pytan_root_dir = os.path.dirname(parent_dir)
        lib_dir = os.path.join(pytan_root_dir, 'lib')

        path_adds = [lib_dir, pytan_static_path]
        [sys.path.append(aa) for aa in path_adds if aa not in sys.path]

        import pytan
        self.pytan = pytan
        self.handler_args = {}

        self.handler_args['username'] = self.config.username
        self.handler_args['password'] = self.config.password
        self.handler_args['host'] = self.config.ip
        self.handler_args['port'] = self.config.port # optional

        self.handler_args['loglevel'] = 1

        self.handler_args['debugformat'] = False

        self.handler_args['record_all_requests'] = True

    def ask_saved_question_by_name(self, args={}):
        handler = self.pytan.Handler(**self.handler_args)

        kwargs = {}
        kwargs["qtype"] = u'saved'
        kwargs["name"] = args["name"]

        response = handler.ask(**kwargs)

        if response['question_results']:
            export_kwargs = {}
            export_kwargs['obj'] = response['question_results']

            export_kwargs['export_format'] = 'json'

            out = handler.export_obj(**export_kwargs)

            return out


    def ask_manual_question_sensor_with_filter1(self, args={}):
        handler = self.pytan.Handler(**self.handler_args)

        kwargs = {}
        kwargs["sensors"] = args["sensors"]
        kwargs["qtype"] = u'manual'

        response = handler.ask(**kwargs)

        if response['question_results']:
            export_kwargs = {}
            export_kwargs['obj'] = response['question_results']
            export_kwargs['export_format'] = 'json'

            out = handler.export_obj(**export_kwargs)

            return out

    def ask_manual_question_with_filter(self, args={}):
        print args["name"]
        return args["name"]

    #Takes 10 minutes to return
	#TODO externalize kwargs["action_filters"]
    def deploy_action_with_params_against_windows_computers(self, args={}):
        handler = self.pytan.Handler(**self.handler_args)

        kwargs = {}
        kwargs["run"] = True
        kwargs["action_filters"] = args["action_filters"]
        print args["sensors"]
        kwargs["sensors"] = args["sensors"]
        kwargs["action_options"] = args["action_options"]
        kwargs["package"] = args["package"]

        response = handler.deploy_action(**kwargs)

        if response['action_results']:
            export_kwargs = {}
            export_kwargs['obj'] = response['action_results']
            export_kwargs['export_format'] = 'json'

            out = handler.export_obj(**export_kwargs)

            return out


    # Every function in Main is an action that can be taken
    # Every function needs to define an args argument which recieves a dictionary of input parameters
    def helloWorld(self, args={}):
        # LOOK AT YOUR CONSOLE WHEN EXECUTING
        print self.introMessage

        return self.introMessage

    # Example using arguments
    # Repeats back the contents of the call argument
    def repeatBackToMe(self, args={}):
        print "REPEATING: " + args["call"]

        return "REPEATING: " + args["call"]

    def shutdown(self):
        print "TANIUM SHUTTING DOWN"
        return