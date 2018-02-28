import walkoff.appgateway


def modified_setup_worker_env():
    import tests.config
    import walkoff.config.config
    from tests.util.execution_db_help import setup_dbs
    import apps
    walkoff.appgateway.cache_apps(tests.config.test_apps_path)
    walkoff.config.config.load_app_apis(apps_path=tests.config.test_apps_path)
    setup_dbs()
