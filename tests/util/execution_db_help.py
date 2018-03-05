import json
import os

import tests.config
import walkoff.config.paths
from tests.config import test_workflows_path
from tests.util.jsonplaybookloader import JsonPlaybookLoader
from walkoff import executiondb
from walkoff import initialize_databases
from walkoff.executiondb.action import Action
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.branch import Branch
from walkoff.executiondb.condition import Condition
from walkoff.executiondb.conditionalexpression import ConditionalExpression
from walkoff.executiondb.playbook import Playbook
from walkoff.executiondb.transform import Transform
from walkoff.executiondb.workflow import Workflow
from walkoff.executiondb.workflowresults import WorkflowStatus


def load_playbooks(playbooks):
    paths = []
    paths.extend([os.path.join(test_workflows_path, filename) for filename in os.listdir(test_workflows_path)
                  if filename.endswith('.playbook') and filename.split('.')[0] in playbooks])
    for path in paths:
        with open(path, 'r') as playbook_file:
            playbook = Playbook.create(json.load(playbook_file))
            executiondb.execution_db.session.add(playbook)
    executiondb.execution_db.session.commit()


def standard_load():
    load_playbooks(['test', 'dataflowTest'])
    return executiondb.execution_db.session.query(Playbook).filter_by(name='test').first()


def load_playbook(playbook_name):
    playbook = JsonPlaybookLoader.load_playbook(os.path.join(test_workflows_path, playbook_name + '.playbook'))
    executiondb.execution_db.session.add(playbook)
    executiondb.execution_db.session.commit()
    return playbook


def load_workflow(playbook_name, workflow_name):
    playbook = JsonPlaybookLoader.load_playbook(os.path.join(test_workflows_path, playbook_name + '.playbook'))
    executiondb.execution_db.session.add(playbook)
    executiondb.execution_db.session.commit()

    workflow = None
    for wf in playbook.workflows:
        if wf.name == workflow_name:
            workflow = wf
            break

    return workflow


def setup_dbs():
    walkoff.config.paths.db_path = tests.config.test_db_path
    walkoff.config.paths.case_db_path = tests.config.test_case_db_path
    walkoff.config.paths.execution_db_path = tests.config.test_execution_db_path
    initialize_databases()


def cleanup_device_db():
    executiondb.execution_db.session.rollback()
    classes = [Playbook, Workflow, Action, Branch, Argument, ConditionalExpression, Condition, Transform]
    for ee in classes:
        for instance in executiondb.execution_db.session.query(ee).all():
            executiondb.execution_db.session.delete(instance)

    for instance in executiondb.execution_db.session.query(WorkflowStatus).all():
        executiondb.execution_db.session.delete(instance)
    executiondb.execution_db.session.commit()


def tear_down_device_db():
    executiondb.execution_db.tear_down()
