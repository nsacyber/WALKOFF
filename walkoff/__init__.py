__version__ = '0.7.0'


def initialize_databases():
    import walkoff.executiondb
    import walkoff.case.database
    import walkoff.config.config
    import walkoff.config.paths

    walkoff.executiondb.execution_db = walkoff.executiondb.ExecutionDatabase(walkoff.config.config.execution_db_type,
                                                                             walkoff.config.paths.execution_db_path)
    walkoff.case.database.case_db = walkoff.case.database.CaseDatabase(walkoff.config.config.case_db_type,
                                                                       walkoff.config.paths.case_db_path)
