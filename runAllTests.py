import unittest
from multiprocessing import freeze_support
from tests import suites as test_suites

if __name__ == '__main__':
    freeze_support()
    print('Testing Workflows:')
    unittest.TextTestRunner(verbosity=1).run(test_suites.workflow_suite)
    print('\nTesting Execution:')
    unittest.TextTestRunner(verbosity=1).run(test_suites.execution_suite)
    print('\nTesting Cases:')
    unittest.TextTestRunner(verbosity=1).run(test_suites.case_suite)
    print('\nTesting Server:')
    unittest.TextTestRunner(verbosity=1).run(test_suites.server_suite)
