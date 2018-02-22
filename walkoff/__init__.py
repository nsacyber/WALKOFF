__version__ = '0.6.7'


def initialize_databases():
    import walkoff.executiondb.devicedb
    import walkoff.case.database

    walkoff.executiondb.devicedb.device_db = walkoff.executiondb.devicedb.DeviceDatabase()
    walkoff.case.database.case_db = walkoff.case.database.CaseDatabase()

