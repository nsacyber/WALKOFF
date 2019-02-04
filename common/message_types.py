class ActionResult:
    """ Class that formats an ActionResult message """
    def __init__(self, action, result=None, error=None):
        self.result = result
        self.execution_id = action["execution_id"]
        self.action_id = action["id"]
        self.name = action["name"]
        self.action_name = action["action_name"]
        self.app_name = action["app_name"]
        self.error = error

    def to_json(self):
        ret = {"execution_id": self.execution_id, "app_name": self.app_name, "action_name": self.action_name,
               "name": self.name, "action_id": self.action_id, "result": self.result, "error": self.error}
        return ret


# class ConfigDetails(namedtuple('_ConfigDetails', 'working_dir config_files environment')):
#     """
#     :param working_dir: the directory to use for relative paths in the config
#     :type  working_dir: string
#     :param config_files: list of configuration files to load
#     :type  config_files: list of :class:`ConfigFile`
#     :param environment: computed environment values for this project
#     :type  environment: :class:`environment.Environment`
#      """
#     def __new__(cls, working_dir, config_files, environment=None):
#         if environment is None:
#             environment = Environment.from_env_file(working_dir)
#         return super(ConfigDetails, cls).__new__(
#             cls, working_dir, config_files, environment
#         )

class AppRepo:
    def __init__(self, app_repo):
        self.app_repo = app_repo
        self.built_apps = {app for app in self.app_repo if app["built"] is True}
    
    def to_json(self):
        return self.app_repo

