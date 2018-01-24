import walkoff.case.database as case_database
from walkoff.case.workflowresults import WorkflowResult
from walkoff.server import flaskserver
from tests.util.servertestcase import ServerTestCase
import walkoff.coredb.devicedb
from walkoff.coredb.playbook import Playbook
from walkoff.coredb.workflow import Workflow


class TestWorkflowResults(ServerTestCase):
    def setUp(self):
        case_database.initialize()

    def tearDown(self):
        case_database.case_db.tear_down()

    def test_workflow_result_format(self):
        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).join(Workflow._playbook).filter(
            Workflow.name == 'multiactionWorkflow', Playbook.name == 'multiactionWorkflowTest').first()
        uid = flaskserver.running_context.controller.execute_workflow(workflow.id)

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
        workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).join(Workflow._playbook).filter(
            Workflow.name == 'multiactionWorkflow', Playbook.name == 'multiactionWorkflowTest').first()

        uid1 = flaskserver.running_context.controller.execute_workflow(workflow.id)
        uid2 = flaskserver.running_context.controller.execute_workflow(workflow.id)

        flaskserver.running_context.controller.wait_and_reset(2)

        workflow_uids = case_database.case_db.session.query(WorkflowResult).with_entities(WorkflowResult.uid).all()
        self.assertSetEqual({uid1, uid2}, {uid[0] for uid in workflow_uids})
