__version__ = '0.6.7'


def initialize_databases():
    import walkoff.executiondb
    import walkoff.case.database

    walkoff.executiondb.execution_db = walkoff.executiondb.ExecutionDatabase()
    walkoff.case.database.case_db = walkoff.case.database.CaseDatabase()

