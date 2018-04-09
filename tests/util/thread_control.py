def modified_setup_worker_env():
    import tests.config
    import walkoff.config
    from tests.util.execution_db_help import setup_dbs
    import apps  # need this import

    walkoff.config.initialize(config_path=tests.config)
    return setup_dbs()
