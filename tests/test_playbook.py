import unittest

import walkoff
from walkoff.core.executionelements.playbook import Playbook
from tests.test_scheduler import MockWorkflow
from tests.util.assertwrappers import orderless_list_compare


class TestPlaybook(unittest.TestCase):
    def test_init(self):
        playbook = Playbook('test')
        self.assertEqual(playbook.name, 'test')
        self.assertIsNotNone(playbook.uid)
        self.assertDictEqual(playbook.workflows, {})
        self.assertEqual(playbook.walkoff_version, walkoff.__version__)

    def test_init_with_workflows(self):
        workflows = [MockWorkflow(i, i + 1) for i in range(3)]
        playbook = Playbook('test', workflows)
        self.assertEqual(playbook.name, 'test')
        self.assertEqual(playbook.walkoff_version, walkoff.__version__)
        orderless_list_compare(self, list(playbook.workflows.keys()), [workflow.name for workflow in workflows])

    def test_init_with_uid(self):
        playbook = Playbook('test', uid='uuu')
        self.assertEqual(playbook.name, 'test')
        self.assertEqual(playbook.uid, 'uuu')
        self.assertDictEqual(playbook.workflows, {})
        self.assertEqual(playbook.walkoff_version, walkoff.__version__)

    def test_init_with_walkoff_version_number(self):
        playbook = Playbook('test', walkoff_version='0.4.0')
        self.assertEqual(playbook.name, 'test')
        self.assertDictEqual(playbook.workflows, {})
        self.assertEqual(playbook.walkoff_version, '0.4.0')

    def test_add_workflow(self):
        workflow = MockWorkflow('uid', 'wf_name')
        playbook = Playbook('test', [workflow])
        playbook.add_workflow(MockWorkflow('uid2', 'test2'))
        orderless_list_compare(self, list(playbook.workflows.keys()), ['wf_name', 'test2'])

    def test_add_workflow_name_already_exists(self):
        workflow = MockWorkflow('uid', 'wf_name')
        playbook = Playbook('test', [workflow])
        playbook.add_workflow(MockWorkflow('uid2', 'wf_name'))
        self.assertEqual(playbook.workflows['wf_name'].uid, 'uid2')

    def test_has_workflow_name_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertFalse(playbook.has_workflow_name('anything'))

    def test_has_workflow_name(self):
        workflow = MockWorkflow('uid', 'wf_name')
        playbook = Playbook('test', [workflow])
        self.assertTrue(playbook.has_workflow_name('wf_name'))

    def test_has_workflow_name_no_name(self):
        workflow = MockWorkflow('uid', 'wf_name')
        playbook = Playbook('test', [workflow])
        self.assertFalse(playbook.has_workflow_name('invalid'))

    def test_has_workflow_uid_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertFalse(playbook.has_workflow_uid('anything'))

    def test_has_workflow_uid(self):
        workflow = MockWorkflow('uid', 'wf_name')
        playbook = Playbook('test', [workflow])
        self.assertTrue(playbook.has_workflow_uid('uid'))

    def test_has_workflow_uid_no_uid(self):
        workflow = MockWorkflow('uid', 'wf_name')
        playbook = Playbook('test', [workflow])
        self.assertFalse(playbook.has_workflow_uid('invalid'))

    def test_get_workflow_by_name_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertIsNone(playbook.get_workflow_by_name('anything'))

    def test_get_workflow_by_name(self):
        workflow = MockWorkflow('uid', 'wf_name')
        playbook = Playbook('test', [workflow])
        self.assertEqual(playbook.get_workflow_by_name('wf_name'), workflow)

    def test_get_workflow_by_name_no_name(self):
        workflow = MockWorkflow('uid', 'wf_name')
        playbook = Playbook('test', [workflow])
        self.assertIsNone(playbook.get_workflow_by_name('invalid'))

    def test_get_workflow_by_uid_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertIsNone(playbook.get_workflow_by_uid('anything'))

    def test_get_workflow_by_uid(self):
        workflow = MockWorkflow('uid', 'wf_name')
        playbook = Playbook('test', [workflow])
        self.assertEqual(playbook.get_workflow_by_uid('uid'), workflow)

    def test_get_workflow_by_uid_no_name(self):
        workflow = MockWorkflow('uid', 'wf_name')
        playbook = Playbook('test', [workflow])
        self.assertIsNone(playbook.get_workflow_by_uid('invalid'))

    def test_get_all_workflow_names_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertListEqual(playbook.get_all_workflow_names(), [])

    def test_get_all_workflow_names(self):
        workflows = [MockWorkflow(i, i + 1) for i in range(3)]
        playbook = Playbook('test', workflows)
        orderless_list_compare(self, playbook.get_all_workflow_names(), list(range(1, 4)))

    def test_get_all_workflow_uids_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertListEqual(playbook.get_all_workflow_uids(), [])

    def test_get_all_workflow_uids(self):
        workflows = [MockWorkflow(i, i + 1) for i in range(3)]
        playbook = Playbook('test', workflows)
        orderless_list_compare(self, playbook.get_all_workflow_uids(), list(range(3)))

    def test_get_all_workflows_as_json_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertListEqual(playbook.get_all_workflow_representations(), [])

    def test_get_all_workflows_as_json(self):
        workflows = [MockWorkflow(i, i + 1) for i in range(3)]
        playbook = Playbook('test', workflows)
        workflow_jsons = playbook.get_all_workflow_representations()
        expected = [{'name': i + 1, 'uid': i, 'other': 'other'} for i in range(3)]
        for workflow_json in workflow_jsons:
            self.assertIn(workflow_json, expected)

    def test_get_all_workflows_as_limited_json_no_workflows(self):
        playbook = Playbook('test', [])
        self.assertListEqual(playbook.get_all_workflows_as_limited_json(), [])

    def test_get_all_workflows_as_limited_json(self):
        workflows = [MockWorkflow(i, i + 1) for i in range(3)]
        playbook = Playbook('test', workflows)
        workflow_jsons = playbook.get_all_workflows_as_limited_json()
        expected = [{'name': i + 1, 'uid': i} for i in range(3)]
        for workflow_json in workflow_jsons:
            self.assertIn(workflow_json, expected)

    def test_rename_workflow_no_workflows(self):
        playbook = Playbook('test', [])
        playbook.rename_workflow('anything', 'renamed')
        self.assertDictEqual(playbook.workflows, {})

    def test_rename_workflow_not_found(self):
        workflows = [MockWorkflow(i, i + 1) for i in range(3)]
        playbook = Playbook('test', workflows)
        playbook.rename_workflow('invalid', 'new_name')
        self.assertTrue(all(playbook.has_workflow_uid(uid) for uid in range(3)))
        self.assertFalse(playbook.has_workflow_name('invalid'))

    def test_rename_workflow(self):
        workflows = [MockWorkflow(i, i + 1) for i in range(3)]
        playbook = Playbook('test', workflows)
        playbook.rename_workflow(3, 'new_name')
        self.assertTrue(playbook.has_workflow_name('new_name'))
        self.assertFalse(playbook.has_workflow_name(3))

    def test_remove_workflow_by_name_no_workflows(self):
        playbook = Playbook('test', [])
        playbook.remove_workflow_by_name('something')
        self.assertDictEqual(playbook.workflows, {})

    def test_remove_workflow_by_name_workflow_not_found(self):
        workflows = [MockWorkflow(i, i + 1) for i in range(3)]
        playbook = Playbook('test', workflows)
        playbook.remove_workflow_by_name('invalid')
        self.assertEqual(len(playbook.workflows), 3)

    def test_remove_workflow_by_name(self):
        workflows = [MockWorkflow(i, i + 1) for i in range(3)]
        playbook = Playbook('test', workflows)
        playbook.remove_workflow_by_name(2)
        self.assertEqual(len(playbook.workflows), 2)
        self.assertFalse(playbook.has_workflow_name(2))
