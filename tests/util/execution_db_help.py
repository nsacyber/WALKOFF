import json
import os

import tests.config
import walkoff.config
from tests.config import test_workflows_path
from tests.util.jsonplaybookloader import JsonPlaybookLoader
from walkoff.executiondb import ExecutionDatabase
from walkoff.case.database import CaseDatabase
from walkoff.executiondb.action import Action
from walkoff.executiondb.argument import Argument
from walkoff.executiondb.branch import Branch
from walkoff.executiondb.condition import Condition
from walkoff.executiondb.conditionalexpression import ConditionalExpression
from walkoff.executiondb.playbook import Playbook
from walkoff.executiondb.schemas import PlaybookSchema
from walkoff.executiondb.transform import Transform
from walkoff.executiondb.workflow import Workflow
from walkoff.executiondb.workflowresults import WorkflowStatus, ActionStatus
from walkoff.executiondb.metrics import AppMetric, WorkflowMetric


def setup_dbs():
    walkoff.config.Config.DB_PATH = tests.config.test_db_path
    walkoff.config.Config.CASE_DB_PATH = tests.config.test_case_db_path
    walkoff.config.Config.EXECUTION_DB_PATH = tests.config.test_execution_db_path

    execution_db = ExecutionDatabase(walkoff.config.Config.EXECUTION_DB_TYPE, walkoff.config.Config.EXECUTION_DB_PATH)
    case_db = CaseDatabase(walkoff.config.Config.CASE_DB_TYPE, walkoff.config.Config.CASE_DB_PATH)

    return execution_db, case_db


def cleanup_execution_db():
    execution_db = ExecutionDatabase.instance
    execution_db.session.rollback()
    classes = [Playbook, Workflow, Action, Branch, Argument, ConditionalExpression, Condition, Transform,
               WorkflowStatus, ActionStatus, AppMetric, WorkflowMetric, WorkflowStatus]
    for ee in classes:
        execution_db.session.query(ee).delete()

    execution_db.session.commit()


def tear_down_execution_db():
    execution_db = ExecutionDatabase.instance
    execution_db.tear_down()


def load_playbooks(playbooks):
    execution_db = ExecutionDatabase.instance
    
    paths = []
    paths.extend([os.path.join(test_workflows_path, filename) for filename in os.listdir(test_workflows_path)
                  if filename.endswith('.playbook') and filename.split('.')[0] in playbooks])
    for path in paths:
        with open(path, 'r') as playbook_file:
            playbook = PlaybookSchema().load(json.load(playbook_file))
            if playbook.errors:
                print(playbook.errors)
                raise Exception('There be errors in yer playbooks')
            execution_db.session.add(playbook.data)
    execution_db.session.commit()


def standard_load():
    execution_db = ExecutionDatabase.instance
    load_playbooks(['test', 'dataflowTest'])
    return execution_db.session.query(Playbook).filter_by(name='test').first()


def load_playbook(playbook_name):
    execution_db = ExecutionDatabase.instance
    playbook = JsonPlaybookLoader.load_playbook(os.path.join(test_workflows_path, playbook_name + '.playbook'))
    execution_db.session.add(playbook)
    execution_db.session.commit()
    return playbook


def load_workflow(playbook_name, workflow_name):
    execution_db = ExecutionDatabase.instance
    playbook = JsonPlaybookLoader.load_playbook(os.path.join(test_workflows_path, playbook_name + '.playbook'))
    execution_db.session.add(playbook)
    execution_db.session.commit()

    workflow = None
    for wf in playbook.workflows:
        if wf.name == workflow_name:
            workflow = wf
            break

    return workflow
