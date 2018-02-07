import json
import os
import os.path
import stat
from unittest import TestCase

from walkoff.coredb.playbook import Playbook
from walkoff.coredb.workflow import Workflow
from walkoff.core.jsonplaybookloader import JsonPlaybookLoader as Loader
from tests.config import test_data_path


class TestJsonPlaybookLoader(TestCase):
    @classmethod
    def setUpClass(cls):
        if not os.path.exists(test_data_path):
            os.mkdir(test_data_path)

    def tearDown(self):
        if os.path.exists(test_data_path):
            for path in os.listdir(test_data_path):
                try:
                    os.remove(os.path.join(test_data_path, path))
                except WindowsError as we:  # Windows sometimes makes files read only when created
                    os.chmod(os.path.join(test_data_path, path), stat.S_IWRITE)
                    os.remove(os.path.join(test_data_path, path))

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(test_data_path):
            for path in os.listdir(test_data_path):
                os.remove(path)
            os.rmdir(test_data_path)

    def test_load_workflow_file_dne(self):
        self.assertIsNone(Loader.load_workflow('/some/invalid/workflow.invalid', 'something'))

    def test_load_workflow_file_bad_permissions(self):
        test_permissions = {'a': 42}
        filepath = os.path.join(test_data_path, 'test.json')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(test_permissions))
        os.chmod(filepath, 0o444)
        self.assertIsNone(Loader.load_workflow(filepath, 'something'))

    def test_load_workflow_invalid_json_format(self):
        test_invalid_json = 'something not json'
        filepath = os.path.join(test_data_path, 'test.json')
        with open(filepath, 'w') as file_out:
            file_out.write(test_invalid_json)
        self.assertIsNone(Loader.load_workflow(filepath, 'something'))

    def test_load_workflow_name_not_in_playbook_json(self):
        test_invalid_json = {'a': 42}
        filepath = os.path.join(test_data_path, 'test.json')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(test_invalid_json))
        self.assertIsNone(Loader.load_workflow(filepath, 'something'))

    def test_load_workflow_with_workflow_not_in_playbook(self):
        playbook = Playbook('test')
        filepath = os.path.join(test_data_path, 'test.json')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(playbook.read()))
        self.assertIsNone(Loader.load_workflow(filepath, 'something'))

    def test_load_workflow_invalid_workflow_json(self):
        workflow_json = {
            "name": "test_workflow",
            "start": "start",
            "actions": [{"action": "repeatBackToMe",
                         "app": "HelloWorld",
                         "name": "start"}]}
        playbook_json = {'name': 'test_playbook', 'workflows': [workflow_json]}
        filepath = os.path.join(test_data_path, 'test.json')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(playbook_json))
        self.assertIsNone(Loader.load_workflow(filepath, 'test_workflow'))

    def test_load_workflow_invalid_app(self):
        workflow_json = {
            "name": "test_workflow",
            "start": "start",
            "actions": [{"action": "invalid",
                         "app": "Invalid",
                         "name": "start",
                         "branches": []}]}
        playbook_json = {'name': 'test_playbook', 'workflows': [workflow_json]}
        filepath = os.path.join(test_data_path, 'test.json')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(playbook_json))
        self.assertIsNone(Loader.load_workflow(filepath, 'test_workflow'))

    def test_load_workflow(self):
        workflows = [Workflow('something'), Workflow('something2')]
        playbook = Playbook('test', workflows=workflows)
        filepath = os.path.join(test_data_path, 'test.json')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(playbook.read()))
        loaded = Loader.load_workflow(filepath, 'something')
        self.assertEqual(loaded[0], 'test')
        self.assertIsInstance(loaded[1], Workflow)
        self.assertEqual(loaded[1].name, 'something')

    def test_load_playbook_file_dne(self):
        self.assertIsNone(Loader.load_playbook('/some/invalid/workflow.invalid'))

    def test_load_playbook_file_bad_permissions(self):
        test_permissions = {'a': 42}
        filepath = os.path.join(test_data_path, 'test.json')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(test_permissions))
        os.chmod(filepath, 0o444)
        self.assertIsNone(Loader.load_playbook(filepath))

    def test_load_playbook_invalid_json_format(self):
        test_invalid_json = 'something not json'
        filepath = os.path.join(test_data_path, 'test.json')
        with open(filepath, 'w') as file_out:
            file_out.write(test_invalid_json)
        self.assertIsNone(Loader.load_playbook(filepath))

    def test_load_playbook_invalid_app(self):
        workflow_json = {
            "name": "test_workflow",
            "start": "start",
            "actions": [{"action": "invalid",
                         "app": "Invalid",
                         "name": "start",
                         "branches": []}]}
        playbook_json = {'name': 'test_playbook', 'workflows': [workflow_json]}
        filepath = os.path.join(test_data_path, 'test.json')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(playbook_json))
        self.assertIsNone(Loader.load_playbook(filepath))

    def test_load_playbook(self):
        workflows = [Workflow('something'), Workflow('something2')]
        playbook = Playbook('test', workflows=workflows)
        filepath = os.path.join(test_data_path, 'test.json')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(playbook.read()))
        loaded = Loader.load_playbook(filepath)
        self.assertIsInstance(loaded, Playbook)
        self.assertEqual(loaded.name, 'test')

    def test_load_playbooks_none_in_directory(self):
        self.assertListEqual(Loader.load_playbooks(test_data_path), [])

    def test_load_playbooks_mixed_files_in_directory(self):
        workflows = [Workflow('something'), Workflow('something2')]
        playbook = Playbook('test', workflows=workflows)
        filepath = os.path.join(test_data_path, 'test.playbook')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(playbook.read()))
        workflows = [Workflow('something'), Workflow('something2')]
        playbook = Playbook('test2', workflows=workflows)
        filepath = os.path.join(test_data_path, 'test2.some_extension')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(playbook.read()))
        loaded = Loader.load_playbooks(test_data_path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].name, 'test')

    def test_load_playbooks_some_invalid_playbooks_in_directory(self):
        workflows = [Workflow('something'), Workflow('something2')]
        playbook = Playbook('test', workflows=workflows)
        filepath = os.path.join(test_data_path, 'test.playbook')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(playbook.read()))
        test_invalid_json = 'something not json'
        filepath = os.path.join(test_data_path, 'test2.playbook')
        with open(filepath, 'w') as file_out:
            file_out.write(test_invalid_json)
        loaded = Loader.load_playbooks(test_data_path)
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].name, 'test')

    def test_load_multiple_workflows(self):
        workflows = [Workflow('something'), Workflow('something2')]
        playbook = Playbook('test', workflows=workflows)
        filepath = os.path.join(test_data_path, 'test.playbook')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(playbook.read()))
        workflows = [Workflow('something'), Workflow('something2')]
        playbook = Playbook('test2', workflows=workflows)
        filepath = os.path.join(test_data_path, 'test2.playbook')
        with open(filepath, 'w') as file_out:
            file_out.write(json.dumps(playbook.read()))
        loaded = Loader.load_playbooks(test_data_path)
        self.assertEqual(len(loaded), 2)
        self.assertSetEqual({playbook.name for playbook in loaded}, {'test', 'test2'})
