from walkoff.scripts.compose_api import compose_api

compose_api()

import unittest
import sys
from tests import suites as test_suites
import logging
import walkoff.server.context


def run_tests():
    logging.disable(logging.CRITICAL)

    ret = True
    print('Testing Integration:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.integration_suite).wasSuccessful()
    print('Testing Workflows:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.workflow_suite).wasSuccessful()
    print('\nTesting Execution:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.execution_suite).wasSuccessful()
    print('\nTesting Cases:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.case_suite).wasSuccessful()
    print('\nTesting Server:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.server_suite).wasSuccessful()
    print('\nTesting Interface:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.interface_suite).wasSuccessful()
    return ret


if __name__ == '__main__':
    try:
        successful = run_tests()
    except KeyboardInterrupt:
        print('\nInterrupted! Ending full test')
        successful = False
    finally:
        walkoff.server.context.running_context.executor.shutdown_pool()
        sys.exit(not successful)
