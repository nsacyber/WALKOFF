import os
import shutil
import threading
import time
import unittest

import walkoff.appgateway
import walkoff.config.config
import walkoff.config.paths
from tests import config
from tests.util import execution_db_help
from tests.util.thread_control import modified_setup_worker_env
from walkoff import executiondb
from walkoff.executiondb.workflowresults import WorkflowStatus, WorkflowStatusEnum
from walkoff.multiprocessedexecutor.multiprocessedexecutor import MultiprocessedExecutor
from walkoff.server import workflowresults  # Need this import
import walkoff.cache
from mock import create_autospec
from walkoff.case.logger import CaseLogger
from walkoff.cache import make_cache
from walkoff.events import WalkoffEvent


class TestZMQCommunication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        execution_db_help.setup_dbs()

        from walkoff.multiprocessedexecutor.multiprocessedexecutor import spawn_worker_processes
        walkoff.config.config.number_processes = 2
        pids = spawn_worker_processes(walkoff.config.config.number_processes,
                                      walkoff.config.config.num_threads_per_process,
                                      walkoff.config.paths.zmq_private_keys_path,
                                      walkoff.config.config.zmq_results_address,
                                      walkoff.config.config.zmq_communication_address,
                                      worker_environment_setup=modified_setup_worker_env)

        cls.executor = MultiprocessedExecutor(make_cache(), create_autospec(CaseLogger))
        cls.executor.initialize_threading(walkoff.config.paths.zmq_public_keys_path,
                                          walkoff.config.paths.zmq_private_keys_path,
                                          walkoff.config.config.zmq_results_address,
                                          walkoff.config.config.zmq_communication_address, pids)
        walkoff.appgateway.cache_apps(config.test_apps_path)
        walkoff.config.config.load_app_apis(apps_path=config.test_apps_path)

    def tearDown(self):
        execution_db_help.cleanup_execution_db()

    @classmethod
    def tearDownClass(cls):
        if config.test_data_path in os.listdir(config.test_path):
            if os.path.isfile(config.test_data_path):
                os.remove(config.test_data_path)
            else:
                shutil.rmtree(config.test_data_path)
        walkoff.appgateway.clear_cache()
        cls.executor.shutdown_pool()
        execution_db_help.tear_down_execution_db()

    '''Request and Result Socket Testing (Basic Workflow Execution)'''

    def test_simple_workflow_execution(self):
        workflow = execution_db_help.load_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        workflow_id = workflow.id

        result = {'called': False}

        @WalkoffEvent.WorkflowExecutionStart.connect
        def started(sender, **data):
            self.assertEqual(sender['id'], str(workflow_id))
            result['called'] = True

        self.executor.execute_workflow(workflow_id)

        self.executor.wait_and_reset(1)

        self.assertTrue(result['called'])

    def test_execute_multiple_workflows(self):
        workflow = execution_db_help.load_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        workflow_id = workflow.id

        capacity = walkoff.config.config.number_processes * walkoff.config.config.num_threads_per_process

        result = {'workflows_executed': 0}

        @WalkoffEvent.WorkflowExecutionStart.connect
        def started(sender, **data):
            self.assertEqual(sender['id'], str(workflow_id))
            result['workflows_executed'] += 1

        for i in range(capacity):
            self.executor.execute_workflow(workflow_id)

        self.executor.wait_and_reset(capacity)

        self.assertEqual(result['workflows_executed'], capacity)

    '''Communication Socket Testing'''

    # def test_pause_and_resume_workflow(self):
    #     execution_id = None
    #     result = {status: False for status in ('paused', 'resumed', 'called')}
    #     workflow = execution_db_help.load_workflow('pauseResumeWorkflowFixed', 'pauseResumeWorkflow')
    #     workflow_id = workflow.id
    #
    #     def pause_resume_thread():
    #         self.executor.pause_workflow(execution_id)
    #         return
    #
    #     @WalkoffEvent.WorkflowPaused.connect
    #     def workflow_paused_listener(sender, **kwargs):
    #         result['paused'] = True
    #         wf_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
    #             execution_id=sender['execution_id']).first()
    #         wf_status.paused()
    #         executiondb.execution_db.session.commit()
    #
    #         self.executor.resume_workflow(execution_id)
    #
    #     @WalkoffEvent.WorkflowResumed.connect
    #     def workflow_resumed_listener(sender, **kwargs):
    #         result['resumed'] = True
    #
    #     @WalkoffEvent.WorkflowExecutionStart.connect
    #     def workflow_started_listener(sender, **kwargs):
    #         self.assertEqual(sender['id'], str(workflow_id))
    #         result['called'] = True
    #
    #     execution_id = self.executor.execute_workflow(workflow_id)
    #
    #     while True:
    #         executiondb.execution_db.session.expire_all()
    #         workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
    #             execution_id=execution_id).first()
    #         if workflow_status and workflow_status.status == WorkflowStatusEnum.running:
    #             threading.Thread(target=pause_resume_thread).start()
    #             time.sleep(0)
    #             break
    #
    #     self.executor.wait_and_reset(1)
    #     for status in ('called', 'paused', 'resumed'):
    #         self.assertTrue(result[status])
