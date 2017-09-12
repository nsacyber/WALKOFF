
def modified_setup_worker_env(self):
    from core.helpers import import_all_apps, import_all_filters, import_all_flags
    import tests.config
    import core.config.config
    import_all_apps(path=tests.config.test_apps_path)
    core.config.config.load_app_apis(apps_path=tests.config.test_apps_path)
    core.config.config.flags = import_all_flags(package='tests.util.flagsfilters')
    core.config.config.filters = import_all_filters(package='tests.util.flagsfilters')
    core.config.config.load_flagfilter_apis(tests.config.function_api_path)