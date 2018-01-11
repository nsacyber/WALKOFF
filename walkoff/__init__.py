__version__ = '0.6.1'


def initialize_databases():
    import walkoff.coredb.devicedb
    import walkoff.case.database

    walkoff.coredb.devicedb.device_db = walkoff.coredb.devicedb.get_device_db()
    walkoff.case.database.case_db = walkoff.case.database.get_case_db()
