import json
import os
from sqlalchemy import and_

from walkoff.coredb import devicedb
from walkoff.coredb.playbook import Playbook
from walkoff.coredb.workflow import Workflow
from tests.config import test_workflows_path_with_generated, test_workflows_path
from walkoff.core.jsonplaybookloader import JsonPlaybookLoader
import walkoff.config.paths
import tests.config
from walkoff import initialize_databases


def load_playbooks(playbooks):
    paths = []
    for directory in (test_workflows_path_with_generated, test_workflows_path):
        paths.extend([os.path.join(directory, filename) for filename in os.listdir(directory)
                      if filename.endswith('.playbook') and filename.split('.')[0] in playbooks])
    for path in paths:
        with open(path, 'r') as playbook_file:
            playbook = Playbook.create(json.load(playbook_file))
            devicedb.device_db.session.add(playbook)
    devicedb.device_db.session.commit()


def standard_load():
    load_playbooks(['test', 'dataflowTest'])
    return devicedb.device_db.session.query(Playbook).filter_by(name='test').first()


def load_playbook(playbook_name):
    JsonPlaybookLoader.load_playbook(os.path.join(test_workflows_path, playbook_name+'.playbook'))
    return devicedb.device_db.session.query(Playbook).filter_by(name=playbook_name).first()


def load_workflow(playbook_name, workflow_name):
    JsonPlaybookLoader.load_playbook(os.path.join(test_workflows_path, playbook_name+'.playbook'))
    return devicedb.device_db.session.query(Workflow).join(Workflow._playbook).filter(and_(
        Workflow.name == workflow_name, Workflow._playbook.name == playbook_name)).first()


def setup_dbs():
    walkoff.config.paths.db_path = tests.config.test_db_path
    walkoff.config.paths.case_db_path = tests.config.test_case_db_path
    walkoff.config.paths.device_db_path = tests.config.test_device_db_path
    initialize_databases()


def cleanup_device_db():
    devicedb.device_db.session.rollback()
    for instance in devicedb.device_db.session.query(Playbook).all():
        devicedb.device_db.session.delete(instance)
    devicedb.device_db.session.commit()


def tear_down_device_db():
    devicedb.device_db.tear_down()
