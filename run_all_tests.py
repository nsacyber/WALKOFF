from walkoff.helpers import compose_api
import walkoff.config
import tests.config

walkoff.config.Config.load_config(tests.config.TestConfig.CONFIG_PATH)
compose_api(walkoff.config.Config)

import unittest
import sys
from tests import suites as test_suites
import logging
import os


def delete_dbs():
    db_paths = (tests.config.TestConfig.EXECUTION_DB_PATH, tests.config.TestConfig.DB_PATH)
    for db in db_paths:
        if os.path.exists(db):
            os.remove(db)


def run_tests():
    logging.disable(logging.CRITICAL)

    ret = True
    print('Testing Integration:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.integration_suite).wasSuccessful()
    print('Testing Workflows:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.workflow_suite).wasSuccessful()
    print('\nTesting Execution:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.execution_suite).wasSuccessful()
    print('\nTesting Server:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.server_suite).wasSuccessful()
    print('\nTesting Interface:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.interface_suite).wasSuccessful()
    return ret


if __name__ == '__main__':
    try:
        delete_dbs()
        successful = run_tests()
    except KeyboardInterrupt:
        print('\nInterrupted! Ending full test')
        successful = False
    finally:
        from flask import current_app

        current_app.running_context.executor.shutdown_pool()
        sys.exit(not successful)
