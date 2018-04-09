import os
import shutil
import unittest
import threading
import time

import walkoff.appgateway
import walkoff.config
from tests import config
from tests.util import execution_db_help
from tests.util.thread_control import modified_setup_worker_env
from walkoff.executiondb.workflowresults import WorkflowStatus, WorkflowStatusEnum
from walkoff.events import WalkoffEvent
from walkoff.case.subscription import Subscription
from walkoff.case.database import Case, Event
from walkoff.server.app import create_app
from walkoff.multiprocessedexecutor.multiprocessedexecutor import spawn_worker_processes
from walkoff.server import workflowresults  # Need this import


class TestZMQCommunication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        walkoff.config.initialize(config_path=config)
        cls.app = create_app(walkoff.config.Config)
        cls.context = cls.app.test_request_context()
        cls.context.push()

        pids = spawn_worker_processes(walkoff.config.Config.NUMBER_PROCESSES,
                                      walkoff.config.Config.NUMBER_THREADS_PER_PROCESS,
                                      walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH,
                                      walkoff.config.Config.ZMQ_RESULTS_ADDRESS,
                                      walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS,
                                      worker_environment_setup=modified_setup_worker_env)
        cls.app.running_context.executor.initialize_threading(walkoff.config.Config.ZMQ_PUBLIC_KEYS_PATH,
                                                              walkoff.config.Config.ZMQ_PRIVATE_KEYS_PATH,
                                                              walkoff.config.Config.ZMQ_RESULTS_ADDRESS,
                                                              walkoff.config.Config.ZMQ_COMMUNICATION_ADDRESS, cls.app,
                                                              pids)

    def tearDown(self):
        execution_db_help.cleanup_execution_db()

    @classmethod
    def tearDownClass(cls):
        if config.DATA_PATH in os.listdir(config.TEST_PATH):
            if os.path.isfile(config.DATA_PATH):
                os.remove(config.DATA_PATH)
            else:
                shutil.rmtree(config.DATA_PATH)
        for class_ in (Case, Event):
            for instance in cls.app.running_context.case_db.session.query(class_).all():
                cls.app.running_context.case_db.session.delete(instance)
        cls.app.running_context.case_db.session.commit()
        walkoff.appgateway.clear_cache()
        cls.app.running_context.executor.shutdown_pool()
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

        self.app.running_context.executor.execute_workflow(workflow_id)

        self.app.running_context.executor.wait_and_reset(1)

        self.assertTrue(result['called'])

    def test_execute_multiple_workflows(self):
        workflow = execution_db_help.load_workflow('basicWorkflowTest', 'helloWorldWorkflow')
        workflow_id = workflow.id

        capacity = walkoff.config.Config.NUMBER_PROCESSES * walkoff.config.Config.NUMBER_THREADS_PER_PROCESS

        result = {'workflows_executed': 0}

        @WalkoffEvent.WorkflowExecutionStart.connect
        def started(sender, **data):
            self.assertEqual(sender['id'], str(workflow_id))
            result['workflows_executed'] += 1

        for i in range(capacity):
            self.app.running_context.executor.execute_workflow(workflow_id)

        self.app.running_context.executor.wait_and_reset(capacity)

        self.assertEqual(result['workflows_executed'], capacity)

    '''Communication Socket Testing'''

    def test_pause_and_resume_workflow(self):
        execution_id = None
        result = {status: False for status in ('paused', 'resumed', 'called')}
        workflow = execution_db_help.load_workflow('pauseResumeWorkflowFixed', 'pauseResumeWorkflow')
        workflow_id = workflow.id

        case = Case(name='name')
        self.app.running_context.case_db.session.add(case)
        self.app.running_context.case_db.session.commit()
        subscriptions = [Subscription(
            id=str(workflow_id),
            events=[WalkoffEvent.WorkflowPaused.signal_name])]
        self.app.running_context.executor.create_case(case.id, subscriptions)
        self.app.running_context.case_logger.add_subscriptions(case.id, [
            Subscription(str(workflow_id), [WalkoffEvent.WorkflowResumed.signal_name])])

        def pause_resume_thread():
            self.app.running_context.executor.pause_workflow(execution_id)
            return

        @WalkoffEvent.WorkflowPaused.connect
        def workflow_paused_listener(sender, **kwargs):
            result['paused'] = True
            wf_status = self.app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
                execution_id=sender['execution_id']).first()
            wf_status.paused()
            self.app.running_context.execution_db.session.commit()

            self.app.running_context.executor.resume_workflow(execution_id)

        @WalkoffEvent.WorkflowResumed.connect
        def workflow_resumed_listener(sender, **kwargs):
            result['resumed'] = True

        @WalkoffEvent.WorkflowExecutionStart.connect
        def workflow_started_listener(sender, **kwargs):
            self.assertEqual(sender['id'], str(workflow_id))
            result['called'] = True

        execution_id = self.app.running_context.executor.execute_workflow(workflow_id)

        while True:
            self.app.running_context.execution_db.session.expire_all()
            workflow_status = self.app.running_context.execution_db.session.query(WorkflowStatus).filter_by(
                execution_id=execution_id).first()
            if workflow_status and workflow_status.status == WorkflowStatusEnum.running:
                threading.Thread(target=pause_resume_thread).start()
                time.sleep(0)
                break

        self.app.running_context.executor.wait_and_reset(1)
        for status in ('called', 'paused', 'resumed'):
            self.assertTrue(result[status])
