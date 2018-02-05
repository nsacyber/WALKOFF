import walkoff.case.database as case_database
from walkoff.case.workflowresults import WorkflowResult
from walkoff.server import flaskserver
from tests.util.servertestcase import ServerTestCase
from tests.util import device_db_help


class TestWorkflowResults(ServerTestCase):
    def setUp(self):
        self.workflow = device_db_help.load_workflow('multiactionWorkflowTest', 'multiactionWorkflow')

    def tearDown(self):
        for result in case_database.case_db.session.query(WorkflowResult).all():
            case_database.case_db.session.delete(result)
        case_database.case_db.session.commit()
        device_db_help.cleanup_device_db()

    def test_workflow_result_format(self):
        uid = flaskserver.running_context.controller.execute_workflow(self.workflow.id)

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
                             {'arguments': [],
                              'app_name': 'HelloWorldBounded',
                              'action_name': 'helloWorld',
                              'type': 'success',
                              'name': 'start',
                              'result': {"status": "Success", "result": {"message": "HELLO WORLD"}}})

    def test_workflow_result_multiple_workflows(self):
        uid1 = flaskserver.running_context.controller.execute_workflow(self.workflow.id)
        uid2 = flaskserver.running_context.controller.execute_workflow(self.workflow.id)

        flaskserver.running_context.controller.wait_and_reset(2)

        workflow_uids = case_database.case_db.session.query(WorkflowResult).with_entities(WorkflowResult.uid).all()
        self.assertSetEqual({uid1, uid2}, {uid[0] for uid in workflow_uids})

