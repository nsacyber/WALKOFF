import unittest
import sys
from multiprocessing import freeze_support
from tests import suites as test_suites

if __name__ == '__main__':
    freeze_support()
    ret = True
    print('Testing Workflows:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.workflow_suite)
    print('\nTesting Execution:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.execution_suite)
    print('\nTesting Cases:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.case_suite)
    print('\nTesting Server:')
    ret &= unittest.TextTestRunner(verbosity=1).run(test_suites.server_suite)
    sys.exit(not ret)
