__version__ = '0.6.7'


def initialize_databases():
    import walkoff.coredb.devicedb
    import walkoff.case.database

    walkoff.coredb.devicedb.device_db = walkoff.coredb.devicedb.DeviceDatabase()
    walkoff.case.database.case_db = walkoff.case.database.CaseDatabase()

