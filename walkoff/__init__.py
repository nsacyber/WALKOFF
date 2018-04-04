__version__ = '0.8.0a2'


def initialize_databases():
    import walkoff.executiondb
    import walkoff.case.database
    import walkoff.config

    walkoff.executiondb.execution_db = walkoff.executiondb.ExecutionDatabase(
        walkoff.config.Config.EXECUTION_DB_TYPE, walkoff.config.Config.EXECUTION_DB_PATH)
    walkoff.case.database.case_db = walkoff.case.database.CaseDatabase(walkoff.config.Config.CASE_DB_TYPE,
                                                                       walkoff.config.Config.CASE_DB_PATH)
