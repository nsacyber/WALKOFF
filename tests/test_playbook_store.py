from copy import deepcopy
from unittest import TestCase

from core.executionelements.playbook import Playbook
from core.executionelements.workflow import Workflow
from core.playbookstore import PlaybookStore


class MockPlaybookLoader(object):
    def __init__(self):
        self.playbook1 = Playbook('play1', workflows=[Workflow('work1'), Workflow('work2')])
        self.playbook2 = Playbook('play2', workflows=[Workflow('work1'), Workflow('work3')])

    def load_workflow(self, resource, workflow_name):
        if resource == 'play1' and self.playbook1.has_workflow_name(workflow_name):
            return resource, self.playbook1.get_workflow_by_name(workflow_name)
        elif resource == 'play2' and self.playbook2.has_workflow_name(workflow_name):
            return resource, self.playbook2.get_workflow_by_name(workflow_name)
        else:
            return None
    
    def load_playbook(self, resource):
        if resource == 'test1':
            return self.playbook1
        elif resource == 'play2':
            return self.playbook2
        else:
            return None
    
    def load_playbooks(self, resource_collection):
        return [self.playbook1, self.playbook2]


class MockElementReader(object):

    @staticmethod
    def read(element):
        return id(element)


class TestPlaybookStore(TestCase):

    def setUp(self):
        self.store = PlaybookStore()
        self.loader = MockPlaybookLoader()

    def assertStoreKeysEqual(self, keys):
        self.assertSetEqual(set(self.store.playbooks.keys()), set(keys))

    def assertPlaybookHasWorkflowName(self, playbook_name, workflow_name):
        self.assertTrue(self.store.playbooks[playbook_name].has_workflow_name(workflow_name))

    def assertPlaybookWorkflowNamesEqual(self, playbook_name, workflows):
        self.assertSetEqual(set(self.store.playbooks[playbook_name].get_all_workflow_names()), set(workflows))

    def test_init(self):
        self.assertDictEqual(self.store.playbooks, {})

    def test_load_workflow_not_found(self):
        self.assertIsNone(self.store.load_workflow('test1', 'invalid', loader=self.loader))

    def test_load_workflow_playbook_not_in_store_empty_store(self):
        self.store.load_workflow('play1', 'work1', loader=self.loader)
        self.assertIn('play1', self.store.playbooks)
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1'})

    def test_load_workflow_playbook_not_in_store(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.load_workflow('play2', 'work3', loader=self.loader)
        self.assertIn('play2', self.store.playbooks)
        self.assertPlaybookWorkflowNamesEqual('play2', {'work3'})

    def test_load_workflow_playbook_in_storage_new_workflows(self):
        copied_playbook = deepcopy(self.loader.playbook1)
        copied_playbook.remove_workflow_by_name('work1')
        self.store.playbooks['play1'] = copied_playbook
        self.store.load_workflow('play1', 'work1', loader=self.loader)
        self.assertIn('play1', self.store.playbooks)
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})

    def test_load_workflow_playbook_in_storage_workflow_in_storage(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.load_workflow('play1', 'work1', loader=self.loader)
        self.assertIn('play1', self.store.playbooks)
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})

    def test_load_playbook_not_found_none_in_store(self):
        self.store.load_playbook('invalid', loader=self.loader)
        self.assertDictEqual(self.store.playbooks, {})

    def test_load_playbook_not_found_some_in_store(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.load_playbook('invalid', loader=self.loader)
        self.assertStoreKeysEqual({'play1'})

    def test_load_playbook_not_in_store(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.load_playbook('play2', loader=self.loader)
        self.assertStoreKeysEqual({'play1', 'play2'})

    def test_load_playbook_already_in_store(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.load_playbook('play1', loader=self.loader)
        self.assertStoreKeysEqual({'play1'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})

    def test_add_playbook_no_playbooks(self):
        self.store.add_playbook(self.loader.playbook1)
        self.assertStoreKeysEqual({'play1'})
        self.assertEqual(self.store.playbooks['play1'], self.loader.playbook1)

    def test_add_playbook_some_playbooks(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.add_playbook(self.loader.playbook2)
        self.assertStoreKeysEqual({'play1', 'play2'})
        self.assertEqual(self.store.playbooks['play2'], self.loader.playbook2)

    def test_add_playbook_same_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.add_playbook(self.loader.playbook1)
        self.assertStoreKeysEqual({'play1'})
        self.assertEqual(self.store.playbooks['play1'], self.loader.playbook1)

    def test_add_workflow_no_playbooks(self):
        workflow = Workflow('work1')
        self.store.add_workflow('play1', workflow)
        self.assertStoreKeysEqual({'play1'})
        self.assertListEqual(self.store.playbooks['play1'].workflows.values(), [workflow])

    def test_add_workflow_playbook_in_store(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        workflow = Workflow('work3')
        self.store.add_workflow('play1', workflow)
        self.assertStoreKeysEqual({'play1'})
        self.assertPlaybookHasWorkflowName('play1', 'work3')

    def test_add_workflow_playbook_not_in_store(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        workflow = Workflow('work3')
        self.store.add_workflow('play2', workflow)
        self.assertSetEqual(set(self.store.playbooks.keys()), {'play1', 'play2'})
        self.assertListEqual(self.store.playbooks['play2'].workflows.values(), [workflow])

    def test_load_playbooks(self):
        self.store.load_playbooks('resource', loader=self.loader)
        self.assertStoreKeysEqual({'play1', 'play2'})

    def test_create_workflow(self):
        self.store.create_workflow('play1', 'work1')
        self.assertStoreKeysEqual({'play1'})
        self.assertPlaybookHasWorkflowName('play1', 'work1')

    def test_create_workflow_playbook_exists(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.create_workflow('play1', 'work3')
        self.assertStoreKeysEqual({'play1'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2', 'work3'})

    def test_create_workflow_playbook_workflow_exist(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        original_uid = self.store.playbooks['play1'].get_workflow_by_name('work1').uid
        self.store.create_workflow('play1', 'work1')
        self.assertNotEqual(self.store.playbooks['play1'].get_workflow_by_name('work1').uid, original_uid)

    def test_create_playbook_empty_store_no_workflows(self):
        self.store.create_playbook('play1')
        self.assertStoreKeysEqual({'play1'})
        self.assertListEqual(self.store.playbooks['play1'].workflows.values(), [])

    def test_create_playbook_empty_store_with_workflows(self):
        workflow = Workflow('work1')
        self.store.create_playbook('play1', [workflow])
        self.assertStoreKeysEqual({'play1'})
        self.assertListEqual(self.store.playbooks['play1'].workflows.values(), [workflow])

    def test_create_playbook_nonempty_store_no_workflows(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.create_playbook('play2')
        self.assertStoreKeysEqual({'play1', 'play2'})
        self.assertListEqual(self.store.playbooks['play2'].workflows.values(), [])

    def test_create_playbook_nonempty_store_with_workflows(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        workflow = Workflow('work1')
        self.store.create_playbook('play2', [workflow])
        self.assertStoreKeysEqual({'play1', 'play2'})
        self.assertListEqual(self.store.playbooks['play2'].workflows.values(), [workflow])

    def test_create_playbook_playbook_already_exists(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        workflow = Workflow('work3')
        self.store.create_playbook('play1', workflows=[workflow])
        self.assertStoreKeysEqual({'play1'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work3'})

    def test_remove_workflow(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertTrue(self.store.remove_workflow('play1', 'work1'))
        self.assertStoreKeysEqual({'play1'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work2'})

    def test_remove_workflow_workflow_not_found(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertFalse(self.store.remove_workflow('play1', 'invalid'))
        self.assertStoreKeysEqual({'play1'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})

    def test_remove_workflow_playbook_not_found(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertFalse(self.store.remove_workflow('invalid', 'work1'))
        self.assertStoreKeysEqual({'play1'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})

    def test_remove_workflow_empty_store(self):
        self.assertFalse(self.store.remove_workflow('play1', 'work1'))
        self.assertStoreKeysEqual(set())

    def test_remove_playbook_empty_store(self):
        self.assertFalse(self.store.remove_playbook('play1'))
        self.assertStoreKeysEqual(set())

    def test_remove_playbook_playbook_not_found(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertFalse(self.store.remove_playbook('invalid'))
        self.assertStoreKeysEqual({'play1'})

    def test_remove_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertTrue(self.store.remove_playbook('play1'))
        self.assertStoreKeysEqual(set())

    def test_get_all_workflows_with_representations_empty_store(self):
        self.assertListEqual(self.store.get_all_workflows(full_representations=True), [])

    def test_get_all_workflows_with_limited_representations_empty_store(self):
        self.assertListEqual(self.store.get_all_workflows(), [])

    def test_get_all_workflows_with_representations(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertListEqual(self.store.get_all_workflows(full_representations=True), [self.loader.playbook1.read()])

    def test_get_all_workflows_with_limited_representations(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        expected = [{'name': 'play1', 'workflows': [{'name': workflow.name, 'uid': workflow.uid}
                                                   for workflow in self.loader.playbook1.workflows.values()]}]
        self.assertListEqual(self.store.get_all_workflows(), expected)

    def test_get_all_workflows_with_representation_custom_reader(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertListEqual(self.store.get_all_workflows(full_representations=True, reader=MockElementReader),
                             [id(self.loader.playbook1)])

    def test_get_all_playbooks_empty_store(self):
        self.assertListEqual(self.store.get_all_playbooks(), [])

    def test_get_all_playbooks(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.assertSetEqual(set(self.store.get_all_playbooks()), {'play1', 'play2'})

    def test_is_workflow_registered(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertTrue(self.store.is_workflow_registered('play1', 'work1'))

    def test_is_workflow_registered_empty_store(self):
        self.assertFalse(self.store.is_workflow_registered('play1', 'work1'))

    def test_is_workflow_registered_invalid_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertFalse(self.store.is_workflow_registered('invalid', 'work1'))

    def test_is_workflow_registered_invalid_workflow(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertFalse(self.store.is_workflow_registered('play1', 'invalid'))

    def test_is_playbook_registered_empty_store(self):
        self.assertFalse(self.store.is_playbook_registered('play1'))

    def test_is_playbook_registered(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertTrue(self.store.is_playbook_registered('play1'))

    def test_is_playbook_registered_invalid_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertFalse(self.store.is_playbook_registered('invalid'))

    def test_update_workflow_name_empty_store(self):
        self.store.update_workflow_name('old_playbook', 'old_workflow', 'new_playbook', 'new_workflow')
        self.assertStoreKeysEqual(set())

    def test_update_workflow_name_invalid_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.update_workflow_name('invalid', 'work1', 'new_playbook', 'new_workflow')
        self.assertStoreKeysEqual({'play1'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})

    def test_update_workflow_name_invalid_workflow(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.update_workflow_name('play1', 'invalid', 'new_playbook', 'new_workflow')
        self.assertStoreKeysEqual({'play1'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})

    def test_update_workflow_name_same_playbook_same_workflow(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.update_workflow_name('play1', 'work1', 'play1', 'work1')
        self.assertStoreKeysEqual({'play1'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})

    def test_update_workflow_name_same_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.update_workflow_name('play1', 'work1', 'play1', 'renamed')
        self.assertStoreKeysEqual({'play1'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'renamed', 'work2'})

    def test_update_workflow_name_new_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.update_workflow_name('play1', 'work1', 'play2', 'renamed')
        self.assertStoreKeysEqual({'play1', 'play2'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work2'})
        self.assertPlaybookWorkflowNamesEqual('play2', {'renamed'})

    def test_update_playbook_name_empty_store(self):
        self.store.update_playbook_name('old_playbook', 'new_playbook')
        self.assertStoreKeysEqual(set())

    def test_update_playbook_name_invalid_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.update_playbook_name('invalid', 'renamed')
        self.assertStoreKeysEqual({'play1'})

    def test_update_playbook_name(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.update_playbook_name('play1', 'renamed')
        self.assertStoreKeysEqual({'renamed'})
        self.assertEqual(self.store.playbooks['renamed'], self.loader.playbook1)

    def test_get_workflow_empty_store(self):
        self.assertIsNone(self.store.get_workflow('play1', 'work1'))

    def test_get_workflow_invalid_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertIsNone(self.store.get_workflow('invalid', 'work1'))

    def test_get_workflow_invalid_workflow(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertIsNone(self.store.get_workflow('play1', 'invalid'))

    def test_get_workflow(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        workflow = self.loader.playbook1.get_workflow_by_name('work1')
        self.assertEqual(self.store.get_workflow('play1', 'work1'), workflow)

    def test_get_playbook_empty_store(self):
        self.assertIsNone(self.store.get_playbook('play1'))

    def test_get_playbook_invalid_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertIsNone(self.store.get_playbook('invalid'))

    def test_get_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.assertEqual(self.store.get_playbook('play1'), self.loader.playbook1)

    def test_get_all_workflows_by_playbook_empty_store(self):
        self.assertListEqual(self.store.get_all_workflows_by_playbook('play1'), [])

    def test_get_all_workflows_by_playbook_invalid_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.assertListEqual(self.store.get_all_workflows_by_playbook('invalid'), [])

    def test_get_all_workflows_by_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.assertSetEqual(set(self.store.get_all_workflows_by_playbook('play2')), {'work1', 'work3'})

    def test_playbook_representation_empty_store(self):
        self.assertIsNone(self.store.get_playbook_representation('play1'))

    def test_playbook_representation_invalid_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.assertIsNone(self.store.get_playbook_representation('invalid'))

    def test_playbook_representation(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.assertDictEqual(self.store.get_playbook_representation('play1'), self.loader.playbook1.read())

    def test_playbook_representation_custom_reader(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.assertEqual(id(self.loader.playbook1), self.loader.playbook1.read(reader=MockElementReader))

    def test_copy_workflow_empty_store(self):
        self.store.copy_workflow('old_playbook', 'new_playbook', 'old_workflow', 'new_workflow')
        self.assertStoreKeysEqual(set())

    def test_copy_workflow_invalid_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.store.copy_workflow('invalid', 'play1', 'old_workflow', 'new_workflow')
        self.assertStoreKeysEqual({'play1', 'play2'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})

    def test_copy_workflow_invalid_workflow(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.store.copy_workflow('play1', 'play3', 'invalid', 'new_workflow')
        self.assertStoreKeysEqual({'play1', 'play2'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})

    def test_copy_workflow_same_playbook_same_workflow(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.store.copy_workflow('play1', 'play1', 'work1', 'work1')
        self.assertStoreKeysEqual({'play1', 'play2'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})

    def test_copy_workflow_same_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.store.copy_workflow('play1', 'play1', 'work1', 'new_work')
        self.assertStoreKeysEqual({'play1', 'play2'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2', 'new_work'})

    def test_copy_workflow_new_playbook_new_playbook_does_not_exist(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.store.copy_workflow('play1', 'play3', 'work1', 'new_work')
        self.assertStoreKeysEqual({'play1', 'play2', 'play3'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})
        self.assertPlaybookWorkflowNamesEqual('play3', {'new_work'})

    def test_copy_workflow_new_playbook_new_playbook_already_exists(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.store.copy_workflow('play1', 'play2', 'work1', 'new_work')
        self.assertStoreKeysEqual({'play1', 'play2'})
        self.assertPlaybookWorkflowNamesEqual('play1', {'work1', 'work2'})
        self.assertPlaybookWorkflowNamesEqual('play2', {'work1', 'work3', 'new_work'})

    def test_copy_playbook_empty_store(self):
        self.store.copy_playbook('old_playbook', 'new_playbook')
        self.assertStoreKeysEqual(set())

    def test_copy_playbook_invalid_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.store.copy_playbook('invalid', 'new_playbook')
        self.assertStoreKeysEqual({'play1', 'play2'})

    def test_copy_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        original_uid = self.loader.playbook1.uid
        self.store.copy_playbook('play1', 'play3')
        self.assertStoreKeysEqual({'play1', 'play2', 'play3'})
        self.assertPlaybookWorkflowNamesEqual('play3', {'work1', 'work2'})
        self.assertNotEqual(self.store.playbooks['play3'].uid, original_uid)

    def test_copy_playbook_new_playbook_already_exists(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        original_uid = self.loader.playbook1.uid
        self.store.copy_playbook('play1', 'play2')
        self.assertStoreKeysEqual({'play1', 'play2'})
        self.assertPlaybookWorkflowNamesEqual('play2', {'work1', 'work2'})
        self.assertNotEqual(self.store.playbooks['play2'].uid, original_uid)

    def test_add_breakpoint_steps_to_workflow_empty_store(self):
        # just to make sure it doesn't error
        self.store.add_workflow_breakpoint_steps('play1', 'work1', ['a', 'b', 'c'])

    def test_add_breakpoint_steps_to_workflow_invalid_playbook(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.store.add_workflow_breakpoint_steps('invalid', 'work1', ['a', 'b', 'c'])
        self.assertListEqual(self.store.playbooks['play1'].get_workflow_by_name('work1').get_breakpoint_steps(), [])
        self.assertListEqual(self.store.playbooks['play2'].get_workflow_by_name('work1').get_breakpoint_steps(), [])

    def test_add_breakpoint_steps_to_workflow_invalid_workflow(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.store.add_workflow_breakpoint_steps('play1', 'invalid', ['a', 'b', 'c'])
        self.assertListEqual(self.store.playbooks['play1'].get_workflow_by_name('work1').get_breakpoint_steps(), [])
        self.assertListEqual(self.store.playbooks['play1'].get_workflow_by_name('work2').get_breakpoint_steps(), [])

    def test_add_breakpoint_steps_to_workflow_empty_steps_none_existing(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.store.add_workflow_breakpoint_steps('play1', 'work1', [])
        self.assertListEqual(self.store.playbooks['play1'].get_workflow_by_name('work1').get_breakpoint_steps(), [])

    def test_add_breakpoint_steps_to_workflow_empty_steps_some_existing(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.store.add_workflow_breakpoint_steps('play1', 'work1', [])
        self.loader.playbook1.get_workflow_by_name('work1').add_breakpoint_steps(['a', 'b', 'c'])
        self.assertSetEqual(set(self.store.playbooks['play1'].get_workflow_by_name('work1').get_breakpoint_steps()),
                            {'a', 'b', 'c'})

    def test_add_breakpoint_steps_to_workflow_none_existing(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.store.add_workflow_breakpoint_steps('play1', 'work1', ['a', 'b', 'c'])
        self.assertSetEqual(set(self.store.playbooks['play1'].get_workflow_by_name('work1').get_breakpoint_steps()),
                            {'a', 'b', 'c'})

    def test_add_breakpoint_steps_to_workflow_some_existing_no_overlap(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.loader.playbook1.get_workflow_by_name('work1').add_breakpoint_steps(['a', 'b', 'c'])
        self.store.add_workflow_breakpoint_steps('play1', 'work1', ['d', 'e', 'f'])
        self.assertSetEqual(set(self.store.playbooks['play1'].get_workflow_by_name('work1').get_breakpoint_steps()),
                            {'a', 'b', 'c', 'd', 'e', 'f'})

    def test_add_breakpoint_steps_to_workflow_some_existing_all_overlap(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.loader.playbook1.get_workflow_by_name('work1').add_breakpoint_steps(['a', 'b', 'c'])
        self.store.add_workflow_breakpoint_steps('play1', 'work1', ['a', 'b', 'c'])
        self.assertSetEqual(set(self.store.playbooks['play1'].get_workflow_by_name('work1').get_breakpoint_steps()),
                            {'a', 'b', 'c'})

    def test_add_breakpoint_steps_to_workflow_some_existing_some_overlap(self):
        self.store.playbooks['play1'] = self.loader.playbook1
        self.store.playbooks['play2'] = self.loader.playbook2
        self.loader.playbook1.get_workflow_by_name('work1').add_breakpoint_steps(['a', 'b', 'c'])
        self.store.add_workflow_breakpoint_steps('play1', 'work1', ['a', 'b', 'e', 'f'])
        self.assertSetEqual(set(self.store.playbooks['play1'].get_workflow_by_name('work1').get_breakpoint_steps()),
                            {'a', 'b', 'c', 'e', 'f'})
