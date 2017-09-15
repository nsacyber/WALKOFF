from unittest import TestLoader, TestSuite
from . import *


def add_tests_to_suite(suite, test_modules):
    suite.addTests([TestLoader().loadTestsFromModule(test_module) for test_module in test_modules])

__case_tests = [test_case_subscriptions, test_case_database, test_case_config_db]
case_suite = TestSuite()
add_tests_to_suite(case_suite, __case_tests)

__server_tests = [test_case_server, test_triggers, test_server, test_scheduler_actions,
                  test_apps_and_devices, test_workflow_server, test_app_blueprint, test_metrics_server,
                  test_scheduledtasks_database, test_scheduledtasks_server, test_authentication, test_roles_server,
                  test_users_server, test_zmq_communication_server]
server_suite = TestSuite()
add_tests_to_suite(server_suite, __server_tests)

__execution_tests = [test_execution_runtime, test_execution_element, test_execution_events, test_execution_modes,
                     test_step, test_helper_functions, test_filter, test_flag, test_next_step,
                     test_instance, test_controller, test_widget_signals, test_metrics,
                     test_app_utilities, test_apps_registration, test_input_validation, test_decorators,
                     test_app_api_validation, test_flag_filter_validation, test_app_event, test_workflow_results,
                     test_roles_pages_database, test_users_roles_database, test_page_roles_cache]
execution_suite = TestSuite()
add_tests_to_suite(execution_suite, __execution_tests)

__workflow_tests = [test_load_workflow, test_simple_workflow, test_workflow_manipulation, test_zmq_communication]
workflow_suite = TestSuite()
add_tests_to_suite(workflow_suite, __workflow_tests)

full_suite = TestSuite()
for tests in [__workflow_tests, __execution_tests, __case_tests, __server_tests]:
    add_tests_to_suite(full_suite, tests)
