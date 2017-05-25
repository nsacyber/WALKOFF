import unittest
from core.helpers import construct_workflow_name_key
from server import flaskserver
import server.workflowresults
from tests.util.assertwrappers import orderless_list_compare


class TestWorkflowResults(unittest.TestCase):
    def setUp(self):
        server.workflowresults.results.clear()
        server.workflowresults.reset_max_results(50)

    def test_workflow_result_recording(self):
        flaskserver.running_context.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        flaskserver.running_context.controller.execute_workflow('loopWorkflow', 'loopWorkflow')
        flaskserver.running_context.controller.execute_workflow('testExecutionWorkflow', 'helloWorldWorkflow')
        self.assertEqual(len(server.workflowresults.results), 3)

        def __get_record(playbook, workflow):
            name = construct_workflow_name_key(playbook, workflow)
            return next((record for record in server.workflowresults.results if record['name'] == name), None)

        input_ouput = {('basicWorkflowTest', 'helloWorldWorkflow'): "REPEATING: Hello World",
                       ('loopWorkflow', 'loopWorkflow'): 'REPEATING: 5',
                       ('testExecutionWorkflow', 'helloWorldWorkflow'): "REPEATING: Hello World"}
        for (playbook, workflow), expected_result in input_ouput.items():
            record = __get_record(playbook, workflow)
            self.assertIsNotNone(record)
            orderless_list_compare(self, list(record.keys()), ['name', 'timestamp', 'result'])
            self.assertIsInstance(record['timestamp'], str)
            self.assertEqual(record['result'], expected_result)

    # def test_reset_max_len_results_greater_than_original(self):
    #     flaskserver.running_context.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')
    #     flaskserver.running_context.controller.execute_workflow('loopWorkflow', 'loopWorkflow')
    #     flaskserver.running_context.controller.execute_workflow('testExecutionWorkflow', 'helloWorldWorkflow')
    #     original = list(server.workflowresults.results)
    #     server.workflowresults.reset_max_results(server.workflowresults.max_results + 5)
    #     self.assertEqual(server.workflowresults.results.maxlen, server.workflowresults.max_results + 5)
    #     self.assertEqual(len(server.workflowresults.results), len(original))
    #     for new, original in zip(server.workflowresults.results, original):
    #         self.assertDictEqual(new, original)

    # def test_reset_max_len_results_less_than_original(self):
    #     print('less')
    #     print('LESSLESSLESSSLESSSLESSS')
    #     print(server.workflowresults.results)
    #     flaskserver.running_context.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')
    #     flaskserver.running_context.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')
    #     flaskserver.running_context.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')
    #     flaskserver.running_context.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')
    #     flaskserver.running_context.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')
    #     print(server.workflowresults.results)
    #     flaskserver.running_context.controller.execute_workflow('loopWorkflow', 'loopWorkflow')
    #     flaskserver.running_context.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')
    #     flaskserver.running_context.controller.execute_workflow('loopWorkflow', 'loopWorkflow')
    #     print('before')
    #     flaskserver.running_context.controller.execute_workflow('testExecutionWorkflow', 'helloWorldWorkflow')
    #     print('after')
    #     flaskserver.running_context.controller.execute_workflow('testExecutionWorkflow', 'helloWorldWorkflow')
    #     flaskserver.running_context.controller.execute_workflow('testExecutionWorkflow', 'helloWorldWorkflow')
    #     print('after after')
    #     print(server.workflowresults.results)
    #     original = list(server.workflowresults.results)
    #     server.workflowresults.reset_max_results(3)
    #     print(server.workflowresults.results)
    #     self.assertEqual(server.workflowresults.results.maxlen, 3)
    #     self.assertEqual(len(server.workflowresults.results), 3)
    #     for new, original in zip(server.workflowresults.results, original[2:]):
    #         self.assertDictEqual(new, original)
    #     print('DONEDONEDONEDONEDONE')

    # def test_reset_max_len_0(self):
    #     flaskserver.running_context.controller.execute_workflow('basicWorkflowTest', 'helloWorldWorkflow')
    #     flaskserver.running_context.controller.execute_workflow('loopWorkflow', 'loopWorkflow')
    #     flaskserver.running_context.controller.execute_workflow('testExecutionWorkflow', 'helloWorldWorkflow')
    #     server.workflowresults.reset_max_results(0)
    #     self.assertEqual(server.workflowresults.results.maxlen, 0)
    #     self.assertEqual(len(server.workflowresults.results), 0)

    # def test_reset_max_len_negative(self):
    #     with self.assertRaises(ValueError):
    #         server.workflowresults.reset_max_results(-1)

    # def test_workflow_result_overflow(self):
    #     server.workflowresults.max_results = 3