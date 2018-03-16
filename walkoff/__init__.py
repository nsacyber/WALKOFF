__version__ = '0.7.0'


def initialize_databases():
    import walkoff.executiondb
    import walkoff.case.database
    import walkoff.config.config

    walkoff.executiondb.execution_db = walkoff.executiondb.ExecutionDatabase(
        walkoff.config.config.Config.EXECUTION_DB_TYPE, walkoff.config.config.Config.EXECUTION_DB_PATH)
    walkoff.case.database.case_db = walkoff.case.database.CaseDatabase(walkoff.config.config.Config.CASE_DB_TYPE,
                                                                       walkoff.config.config.Config.CASE_DB_PATH)
