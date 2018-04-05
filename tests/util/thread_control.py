import walkoff.appgateway


def modified_setup_worker_env():
    import tests.config
    import walkoff.config
    from tests.util.execution_db_help import setup_dbs
    import apps  # need this import

    walkoff.config.Config.load_config(config_path=tests.config.TEST_CONFIG_PATH)
    walkoff.appgateway.cache_apps(walkoff.config.Config.APPS_PATH)
    walkoff.config.load_app_apis(apps_path=walkoff.config.Config.APPS_PATH)

    return setup_dbs()
