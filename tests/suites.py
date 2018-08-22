from unittest import TestLoader, TestSuite

from . import *


def add_tests_to_suite(suite, test_modules):
    suite.addTests([TestLoader().loadTestsFromModule(test_module) for test_module in test_modules])

__server_tests = [test_workflow_server, test_app_api_server, test_configuration_server,
                  test_scheduler_actions, test_device_server, test_app_blueprint, test_metrics_server,
                  test_scheduledtasks_database, test_scheduledtasks_server, test_authentication, test_roles_server,
                  test_users_server, test_message_history_database, test_message_db, test_message,
                  test_messaging_endpoints, test_trigger_helpers,
                  test_redis_cache_adapter, test_redis_subscription, test_sse_stream,
                  test_filtered_sse_stream, test_notification_stream, test_workflow_status, test_problem,
                  test_workflow_results_stream, test_streamable_blueprint, test_console_stream,
                  test_make_cache, test_health_endpoint]
server_suite = TestSuite()
add_tests_to_suite(server_suite, __server_tests)

__execution_tests = [test_validatable, test_argument, test_action, test_helper_functions,
                     test_workflow_results_handler, test_make_cache,
                     test_workflow_communication_receiver, test_workflow_receiver,
                     test_transform, test_condition, test_branch, test_app_instance, test_metrics, test_app_utilities,
                     test_input_validation, test_decorators, test_app_api_validation, test_playbook,
                     test_condition_transform_validation, test_roles_pages_database, test_users_roles_database,
                     test_scheduler, test_walkoff_tag, test_app_cache, test_app_base, test_console_logging_handler,
                     test_workflow_execution_controller, test_device_database, test_device_field_database,
                     test_action_exec_strategy_factory, test_accumulators, test_accumulator_factory]

execution_suite = TestSuite()
add_tests_to_suite(execution_suite, __execution_tests)

__workflow_tests = [test_simple_workflow, test_workflow_manipulation, test_environment_variable]
workflow_suite = TestSuite()
add_tests_to_suite(workflow_suite, __workflow_tests)

__integration_tests = [test_zmq_communication, test_zmq_communication_server, test_triggers_server]
integration_suite = TestSuite()
add_tests_to_suite(integration_suite, __integration_tests)

__interface_tests = [test_callback_container, test_interface_event_dispatch_helpers, test_app_action_event_dispatcher,
                     test_app_event_dispatcher, test_event_dispatcher, test_interface_event_dispatcher, test_events]
interface_suite = TestSuite()
add_tests_to_suite(interface_suite, __interface_tests)

full_suite = TestSuite()
for tests in [__workflow_tests, __execution_tests, __server_tests, __interface_tests]:
    add_tests_to_suite(full_suite, tests)
