import unittest

from tests.util import execution_db_help, initialize_test_config
from tests.util.assertwrappers import orderless_list_compare
from walkoff.executiondb.playbook import Playbook
from walkoff.executiondb.workflow import Workflow


class TestPlaybook(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        initialize_test_config()
        execution_db_help.setup_dbs()

    @classmethod
    def tearDownClass(cls):
        execution_db_help.tear_down_execution_db()

    def setUp(self):
        self.added_workflows = ['wf_name', '0', '1', '2', 'test2', 'new_name']

    def tearDown(self):
        execution_db_help.cleanup_execution_db()

    def test_init(self):
        playbook = Playbook('test')
        self.assertEqual(playbook.name, 'test')
        self.assertListEqual(playbook.workflows, [])

    def test_init_with_workflows(self):
        workflows = [Workflow(str(i), 0) for i in range(3)]
        playbook = Playbook('test', workflows)
        self.assertEqual(playbook.name, 'test')
        self.assertListEqual(playbook.workflows, workflows)

    def test_add_workflow(self):
        workflow = Workflow('wf_name', 0)
        playbook = Playbook('test', [workflow])
        playbook.add_workflow(Workflow('test2', 0))
        orderless_list_compare(self, [workflow.name for workflow in playbook.workflows], ['wf_name', 'test2'])

    def test_has_workflow_name_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertFalse(playbook.has_workflow_name('anything'))

    def test_has_workflow_name(self):
        workflow = Workflow('wf_name', 0)
        playbook = Playbook('test', [workflow])
        self.assertTrue(playbook.has_workflow_name('wf_name'))

    def test_has_workflow_name_no_name(self):
        workflow = Workflow('wf_name', 0)
        playbook = Playbook('test', [workflow])
        self.assertFalse(playbook.has_workflow_name('invalid'))

    def test_has_workflow_id_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertFalse(playbook.has_workflow_id(1))

    def test_has_workflow_id(self):
        workflow = Workflow('wf_name', 0)
        playbook = Playbook('test', [workflow])
        self.assertTrue(playbook.has_workflow_id(workflow.id))

    def test_get_workflow_by_name_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertIsNone(playbook.get_workflow_by_name('anything'))

    def test_get_workflow_by_name(self):
        workflow = Workflow('wf_name', 0)
        playbook = Playbook('test', [workflow])
        self.assertEqual(playbook.get_workflow_by_name('wf_name'), workflow)

    def test_get_workflow_by_name_no_name(self):
        workflow = Workflow('wf_name', 0)
        playbook = Playbook('test', [workflow])
        self.assertIsNone(playbook.get_workflow_by_name('invalid'))

    def test_get_workflow_by_id_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertIsNone(playbook.get_workflow_by_id('anything'))

    def test_get_workflow_by_id(self):
        workflow = Workflow('wf_name', 0)
        playbook = Playbook('test', [workflow])
        self.assertEqual(playbook.get_workflow_by_id(workflow.id), workflow)

    def test_get_all_workflow_names_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertListEqual(playbook.get_all_workflow_names(), [])

    def test_get_all_workflow_names(self):
        workflows = [Workflow(str(i), 0) for i in range(3)]
        playbook = Playbook('test', workflows)
        orderless_list_compare(self, playbook.get_all_workflow_names(), ['0', '1', '2'])

    def test_get_all_workflow_ids_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertListEqual(playbook.get_all_workflow_ids(), [])

    def test_get_all_workflow_ids(self):
        workflows = [Workflow(str(i), 0) for i in range(3)]
        playbook = Playbook('test', workflows)
        orderless_list_compare(self, playbook.get_all_workflow_ids(), list(workflow.id for workflow in workflows))

    def test_get_all_workflows_as_json_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertListEqual(playbook.get_all_workflow_representations(), [])

    def test_rename_workflow_no_workflows(self):
        playbook = Playbook('test', [])
        playbook.rename_workflow('anything', 'renamed')
        self.assertListEqual(playbook.workflows, [])

    def test_rename_workflow_not_found(self):
        workflows = [Workflow(str(i), 0) for i in range(3)]
        playbook = Playbook('test', workflows)
        playbook.rename_workflow('invalid', 'new_name')
        self.assertFalse(playbook.has_workflow_name('invalid'))

    def test_rename_workflow(self):
        workflows = [Workflow(str(i), 0) for i in range(3)]
        playbook = Playbook('test', workflows)
        playbook.rename_workflow('2', 'new_name')
        self.assertTrue(playbook.has_workflow_name('new_name'))
        self.assertFalse(playbook.has_workflow_name('2'))

    def test_remove_workflow_by_name_no_workflows(self):
        playbook = Playbook('test', [])
        playbook.remove_workflow_by_name('something')
        self.assertListEqual(playbook.workflows, [])

    def test_remove_workflow_by_name_workflow_not_found(self):
        workflows = [Workflow(str(i), 0) for i in range(3)]
        playbook = Playbook('test', workflows)
        playbook.remove_workflow_by_name('invalid')
        self.assertEqual(len(playbook.workflows), 3)

    def test_remove_workflow_by_name(self):
        workflows = [Workflow(str(i), 0) for i in range(3)]
        playbook = Playbook('test', workflows)
        playbook.remove_workflow_by_name('2')
        self.assertEqual(len(playbook.workflows), 2)
        self.assertFalse(playbook.has_workflow_name('2'))
