from core.helpers import construct_workflow_name_key
from server import flaskserver
import server.workflowresults
from tests import config
from tests.util.servertestcase import ServerTestCase

class TestWorkflowResults(ServerTestCase):
    def setUp(self):
        server.workflowresults.results.clear()

    def test_workflow_result_recording(self):
        flaskserver.running_context.controller.load_workflows_from_file(path=config.test_workflows_path +
                                                                        'multiactionWorkflowTest.playbook')
        multiaction_key = construct_workflow_name_key('multiactionWorkflowTest', 'multiactionWorkflow')
        flaskserver.running_context.controller.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        with flaskserver.running_context.flask_app.app_context():
            flaskserver.running_context.shutdown_threads()
        self.assertEqual(len(server.workflowresults.results), 1)
        key = list(server.workflowresults.results.keys())[0]
        self.assertIn('status', server.workflowresults.results[key])
        self.assertEqual(server.workflowresults.results[key]['status'], 'completed')
        self.assertIn('name', server.workflowresults.results[key])
        self.assertEqual(server.workflowresults.results[key]['name'], multiaction_key)
        self.assertIn('completed_at', server.workflowresults.results[key])
        self.assertIn('started_at', server.workflowresults.results[key])
        self.assertIn('results', server.workflowresults.results[key])
        self.assertEqual(len(server.workflowresults.results[key]['results']), 2)
        self.assertEqual(len(server.workflowresults.results[key]['results']), 2)