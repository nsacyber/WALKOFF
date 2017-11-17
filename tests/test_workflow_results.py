import core.case.database as case_database
from core.case.workflowresults import WorkflowResult
from server import flaskserver
from tests import config
from tests.util.servertestcase import ServerTestCase


class TestWorkflowResults(ServerTestCase):
    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.tear_down()

    def test_workflow_result_format(self):
        flaskserver.running_context.controller.load_playbook(resource=config.test_workflows_path +
                                                                        'multiactionWorkflowTest.playbook')
        uid = flaskserver.running_context.controller.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        with flaskserver.running_context.flask_app.app_context():
            flaskserver.running_context.controller.wait_and_reset(1)

        workflow_results = case_database.case_db.session.query(WorkflowResult).all()
        self.assertEqual(len(workflow_results), 1)
        workflow_result = workflow_results[0]
        self.assertEqual(workflow_result.uid, uid)
        self.assertEqual(workflow_result.status, 'completed')
        self.assertEqual(len(workflow_result.results.all()), 2)

        def strip_timestamp(result):
            result.pop('timestamp')
            return result
        self.assertDictEqual(strip_timestamp(workflow_result.results[0].as_json()),
                             {'input': {},
                              'app_name': 'HelloWorld',
                              'action_name': 'helloWorld',
                              'type': 'success',
                              'name': 'start',
                              'result': {"status": "Success", "result": {"message": "HELLO WORLD"}}})

    def test_workflow_result_multiple_workflows(self):
        flaskserver.running_context.controller.load_playbook(resource=config.test_workflows_path +
                                                                             'multiactionWorkflowTest.playbook')
        uid1 = flaskserver.running_context.controller.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        uid2 = flaskserver.running_context.controller.execute_workflow('multiactionWorkflowTest', 'multiactionWorkflow')
        with flaskserver.running_context.flask_app.app_context():
            flaskserver.running_context.controller.wait_and_reset(2)

        workflow_uids = case_database.case_db.session.query(WorkflowResult).with_entities(WorkflowResult.uid).all()
        self.assertSetEqual({uid1, uid2}, {uid[0] for uid in workflow_uids})
