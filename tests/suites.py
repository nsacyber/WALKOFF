from unittest import TestLoader, TestSuite
from tests import *

__case_tests = [testCaseSubscriptions, testCaseDatabase]
case_suite = TestSuite()
case_suite.addTests([TestLoader().loadTestsFromModule(test_module)
                     for test_module in __case_tests])

__server_tests = [#testCaseServer, testStreaming, testTriggers, testUsersAndRoles, testServer, testAppsAndDevices,
                  testWorkflowServer]
server_suite = TestSuite()
server_suite.addTests([TestLoader().loadTestsFromModule(test_module)
                       for test_module in __server_tests])

__execution_tests = [testExecutionRuntime, testExecutionElement, testExecutionEvents, testExecutionModes,
                     testStep, testHelperFunctions, testFilter, testArgument]
execution_suite = TestSuite()
execution_suite.addTests([TestLoader().loadTestsFromModule(test_module)
                          for test_module in __execution_tests])

__workflow_tests = [testLoadWorkflow, testSimpleWorkflow, testWorkflowManipulation]
workflow_suite = TestSuite()
workflow_suite.addTests([TestLoader().loadTestsFromModule(test_module)
                         for test_module in __workflow_tests])
