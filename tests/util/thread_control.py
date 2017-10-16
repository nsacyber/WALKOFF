
def modified_setup_worker_env(self):
    from core.helpers import import_all_apps, import_all_transforms, import_all_conditions
    import tests.config
    import core.config.config
    import_all_apps(path=tests.config.test_apps_path)
    core.config.config.load_app_apis(apps_path=tests.config.test_apps_path)
    core.config.config.conditions = import_all_conditions(package='tests.util.conditionstransforms')
    core.config.config.transforms = import_all_transforms(package='tests.util.conditionstransforms')
    core.config.config.load_condition_transform_apis(tests.config.function_api_path)