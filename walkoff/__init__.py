__version__ = '0.6.1'


def initialize_databases():
    from walkoff.coredb import devicedb
    from walkoff.case import database

    devicedb.device_db = devicedb.get_device_db()
    database.case_db = database.get_case_db()
