import walkoff.appgateway


def modified_setup_worker_env():
    import tests.config
    import walkoff.config
    from tests.util.execution_db_help import setup_dbs
    import apps  # need this import
    import walkoff.cache

    walkoff.appgateway.cache_apps(tests.config.test_apps_path)
    walkoff.config.load_app_apis(apps_path=tests.config.test_apps_path)
    walkoff.config.Config.CACHE = {'type': 'disk', 'directory': tests.config.cache_path}

    return setup_dbs()
