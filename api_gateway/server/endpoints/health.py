from flask import current_app

from api_gateway.extensions import db


def check_cache():
    current_app.running_context.cache.ping()
    return True, 'Cache ok'


def _check_db(db):
    db.session.query('1').from_statement('SELECT 1').all()


def check_server_db():
    _check_db(db)
    return True, 'Server Database ok'


def check_execution_db():
    _check_db(current_app.running_context.execution_db)
    return True, 'Execution Database ok'


checks = [check_cache, check_server_db, check_execution_db]
