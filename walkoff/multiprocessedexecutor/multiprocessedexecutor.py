import logging
import threading
import uuid

import gevent
import nacl.bindings
import nacl.utils
import zmq.green as zmq
from flask import current_app
from nacl.public import PrivateKey, Box

import walkoff.config
from start_workers import shutdown_procs
from walkoff.appgateway.accumulators import make_accumulator
from walkoff.events import WalkoffEvent
from walkoff.executiondb import ExecutionDatabase
from walkoff.executiondb import WorkflowStatusEnum
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.executiondb.workflow import Workflow
from walkoff.executiondb.workflowresults import WorkflowStatus
from walkoff.multiprocessedexecutor.threadauthenticator import ThreadAuthenticator
from walkoff.senders_receivers_helpers import make_results_receiver, make_results_sender, make_communication_sender
from walkoff.worker.action_exec_strategy import make_execution_strategy
from walkoff.worker.workflow_exec_context import RestrictedWorkflowContext

logger = logging.getLogger(__name__)


class MultiprocessedExecutor(object):
    def __init__(self, cache, config):
        """Initializes a multiprocessed executor, which will handle the execution of workflows.
        """
        self.threading_is_initialized = False
        self.id = "controller"
        self.pids = None
        self.workflows_executed = 0

        self.ctx = None  # TODO: Test if you can always use the singleton
        self.auth = None

        self.zmq_workflow_comm = None
        self.receiver = None
        self.receiver_thread = None
        self.cache = cache
        self.config = config
        self.execution_db = ExecutionDatabase.instance
        self.results_sender = None

        key = PrivateKey(walkoff.config.Config.SERVER_PRIVATE_KEY[:nacl.bindings.crypto_box_SECRETKEYBYTES])
        worker_key = PrivateKey(
            walkoff.config.Config.CLIENT_PRIVATE_KEY[:nacl.bindings.crypto_box_SECRETKEYBYTES]).public_key
        self.__box = Box(key, worker_key)

    def initialize_threading(self, app, pids=None):
        """Initialize the multiprocessing communication threads, allowing for parallel execution of workflows.

        Args:
            app (FlaskApp): The current_app object
            pids (list[Process], optional): Optional list of spawned processes. Defaults to None

        """
        if walkoff.config.Config.SEPARATE_RECEIVER:
            pass

        self.pids = pids

        if 'zmq' in [walkoff.config.Config.WORKFLOW_COMMUNICATION_HANDLER,
                     walkoff.config.Config.WORKFLOW_RESULTS_HANDLER]:
            # Only run the threadauthenticator if ZMQ is in use
            self.ctx = zmq.Context.instance()
            self.auth = ThreadAuthenticator()
            self.auth.start()
            # TODO: self.auth.allow('127.0.0.1')
            self.auth.configure_curve(domain='*', location=walkoff.config.Config.ZMQ_PUBLIC_KEYS_PATH)

        self.zmq_workflow_comm = make_communication_sender()

        with app.app_context():
            data = {'execution_db': current_app.running_context.execution_db}
            self.results_sender = make_results_sender(**data)

        if not walkoff.config.Config.SEPARATE_RECEIVER:
            data = {'current_app': app}
            self.receiver = make_results_receiver(**data)

            self.receiver_thread = threading.Thread(target=self.receiver.receive_results)
            self.receiver_thread.start()

        self.threading_is_initialized = True
        logger.debug('Controller threading initialized')

    def wait_and_reset(self, num_workflows):
        """Waits for all of the workflows to be completed

        Args:
            num_workflows (int): The number of workflows to wait for
        """
        timeout = 0
        shutdown = 10

        while timeout < shutdown:
            if self.receiver is not None and num_workflows == self.receiver.workflows_executed:
                break
            timeout += 0.1
            gevent.sleep(0.1)
        assert (num_workflows == self.receiver.workflows_executed)
        self.receiver.workflows_executed = 0

    def shutdown_pool(self):
        """Shuts down the threadpool"""
        if self.zmq_workflow_comm:
            self.zmq_workflow_comm.send_exit_to_workers()
        if not walkoff.config.Config.SEPARATE_WORKERS:
            shutdown_procs(self.pids)

        if self.receiver_thread:
            self.receiver.thread_exit = True
            self.receiver_thread.join(timeout=1)
        self.threading_is_initialized = False
        logger.debug('Controller thread pool shutdown')

        if self.auth:
            self.auth.stop()
        if self.ctx:
            self.ctx.destroy()
        self.cleanup_threading()

        self.execution_db.tear_down()
        return

    def cleanup_threading(self):
        """Once the threadpool has been shutdown, clear out all of the data structures used in the pool"""
        self.pids = []
        self.receiver_thread = None
        self.workflows_executed = 0
        self.threading_is_initialized = False
        self.zmq_workflow_comm = None
        self.receiver = None

    def execute_workflow(self, workflow_id, execution_id_in=None, start=None, start_arguments=None, resume=False,
                         environment_variables=None, user=None):
        """Executes a workflow

        Args:
            workflow_id (Workflow): The Workflow to be executed.
            execution_id_in (UUID, optional): The optional execution ID to provide for the workflow. Should only be
                used (and is required) when resuming a workflow. Must be valid UUID4. Defaults to None.
            start (UUID, optional): The ID of the first, or starting action. Defaults to None.
            start_arguments (list[Argument]): The arguments to the starting action of the workflow. Defaults to None.
            resume (bool, optional): Optional boolean to resume a previously paused workflow. Defaults to False.
            environment_variables (list[EnvironmentVariable]): Optional list of environment variables to pass into
                the workflow. These will not be persistent.
            user (str, Optional): The username of the user who requested that this workflow be executed. Defaults
                to None.

        Returns:
            (UUID): The execution ID of the Workflow.
        """
        workflow = self.execution_db.session.query(Workflow).filter_by(id=workflow_id).first()
        if not workflow:
            logger.error('Attempted to execute workflow {} which does not exist'.format(execution_id_in))
            return None, 'Attempted to execute workflow which does not exist'

        execution_id = execution_id_in if execution_id_in else str(uuid.uuid4())

        if start is not None:
            logger.info('User {0} executing workflow {1} (id={2}) with starting action {3}'.format(
                user, workflow.name, workflow.id, start))
        else:
            logger.info('User {0} executing workflow {1} (id={2}) with default starting action {3}'.format(
                user, workflow.name, workflow.id, workflow.start))

        workflow_data = {'execution_id': execution_id, 'id': str(workflow.id), 'name': workflow.name}

        data = {}
        if user:
            data['user'] = user
        self._log_and_send_event(WalkoffEvent.WorkflowExecutionPending, sender=workflow_data, workflow=workflow,
                                 data=data)
        self.__add_workflow_to_queue(workflow.id, execution_id, start, start_arguments, resume, environment_variables,
                                     user)

        self._log_and_send_event(WalkoffEvent.SchedulerJobExecuted, data=data)
        return execution_id

    def __add_workflow_to_queue(self, workflow_id, workflow_execution_id, start=None, start_arguments=None,
                                resume=False, environment_variables=None, user=None):
        message = self.results_sender.create_workflow_request_message(workflow_id, workflow_execution_id, start,
                                                                      start_arguments, resume, environment_variables,
                                                                      user)
        self.cache.lpush("request_queue", self.__box.encrypt(message))

    def pause_workflow(self, execution_id, user=None):
        """Pauses a workflow that is currently executing.

        Args:
            execution_id (UUID): The execution id of the workflow.

        Returns:
            (bool): True if Workflow successfully paused, False otherwise
        """
        logger.info('User {0} pausing workflow {1}'.format(user, execution_id))
        workflow_status = self.execution_db.session.query(WorkflowStatus).filter_by(execution_id=execution_id).first()
        if workflow_status and workflow_status.status == WorkflowStatusEnum.running:
            self.zmq_workflow_comm.pause_workflow(execution_id)
            return True
        else:
            logger.warning('Cannot pause workflow {0}. Invalid key, or workflow not running.'.format(execution_id))
            return False

    def resume_workflow(self, execution_id, user=None):
        """Resumes a workflow that is currently paused.

        Args:
            execution_id (UUID): The execution id of the workflow.
            user (str, Optional): The username of the user who requested that this workflow be resumed. Defaults
                to None.

        Returns:
            (bool): True if workflow successfully resumed, False otherwise
        """
        logger.info('User {0} resuming workflow {1}'.format(user, execution_id))
        workflow_status = self.execution_db.session.query(WorkflowStatus).filter_by(execution_id=execution_id).first()

        if workflow_status and workflow_status.status == WorkflowStatusEnum.paused:
            saved_state = self.execution_db.session.query(SavedWorkflow).filter_by(
                workflow_execution_id=execution_id).first()
            workflow = self.execution_db.session.query(Workflow).filter_by(id=workflow_status.workflow_id).first()

            data = {"execution_id": execution_id}
            if user:
                data['user'] = user
            self._log_and_send_event(WalkoffEvent.WorkflowResumed, sender=workflow, data=data)

            start = saved_state.action_id if saved_state else workflow.start
            self.execute_workflow(workflow.id, execution_id_in=execution_id, start=start, resume=True, user=user)
            return True
        else:
            logger.warning('Cannot resume workflow {0}. Invalid key, or workflow not paused.'.format(execution_id))
            return False

    def abort_workflow(self, execution_id, user=None):
        """Abort a workflow

        Args:
            execution_id (UUID): The execution id of the workflow.
            user (str, Optional): The username of the user who requested that this workflow be aborted. Defaults
                to None.

        Returns:
            (bool): True if successfully aborted workflow, False otherwise
        """
        logger.info('User {0} aborting workflow {1}'.format(user, execution_id))
        workflow_status = self.execution_db.session.query(WorkflowStatus).filter_by(execution_id=execution_id).first()

        if workflow_status:
            if workflow_status.status in [WorkflowStatusEnum.pending, WorkflowStatusEnum.paused,
                                          WorkflowStatusEnum.awaiting_data]:
                workflow = self.execution_db.session.query(Workflow).filter_by(id=workflow_status.workflow_id).first()
                if workflow is not None:
                    data = {}
                    if user:
                        data['user'] = user
                    self._log_and_send_event(WalkoffEvent.WorkflowAborted,
                                             sender={'execution_id': execution_id, 'id': workflow_status.workflow_id,
                                                     'name': workflow.name}, workflow=workflow, data=data)
            elif workflow_status.status == WorkflowStatusEnum.running:
                self.zmq_workflow_comm.abort_workflow(execution_id)
            return True
        else:
            logger.warning(
                'Cannot resume workflow {0}. Invalid key, or workflow already shutdown.'.format(execution_id))
            return False

    def resume_trigger_step(self, execution_id, data_in, arguments=None, user=None):
        """Resumes a workflow awaiting trigger data, if the conditions are met.

        Args:
            execution_id (UUID): The execution ID of the workflow
            data_in (dict): The data to send to the trigger
            arguments (list[Argument], optional): Optional list of new Arguments for the trigger action.
                Defaults to None.
            user (str, Optional): The username of the user who requested that this workflow be resumed. Defaults
                to None.

        Returns:
            (bool): True if successfully resumed trigger step, false otherwise
        """
        logger.info('User {0} resuming workflow {1} from trigger'.format(user, execution_id))
        saved_state = self.execution_db.session.query(SavedWorkflow).filter_by(
            workflow_execution_id=execution_id).first()
        workflow = self.execution_db.session.query(Workflow).filter_by(id=saved_state.workflow_id).first()

        action_execution_strategy = make_execution_strategy(
            self.config,
            RestrictedWorkflowContext.from_workflow(workflow, execution_id)
        )

        accumulator = make_accumulator(execution_id)
        executed = False
        exec_action = None
        for action in workflow.actions:
            if action.id == saved_state.action_id:
                exec_action = action
                executed = action.execute_trigger(action_execution_strategy, data_in, accumulator)
                break

        data = {'workflow_execution_id': execution_id}
        if user:
            data['user'] = user

        if executed:

            self._log_and_send_event(WalkoffEvent.TriggerActionTaken, sender=exec_action,
                                     data={'workflow_execution_id': execution_id}, workflow=workflow)
            self.execute_workflow(workflow.id, execution_id_in=execution_id, start=str(saved_state.action_id),
                                  start_arguments=arguments, resume=True, user=user)
            return True
        else:
            self._log_and_send_event(WalkoffEvent.TriggerActionNotTaken, sender=exec_action,
                                     data={'workflow_execution_id': execution_id}, workflow=workflow)
            return False

    def get_waiting_workflows(self):
        """Gets a list of the execution IDs of workflows currently awaiting data to be sent to a trigger.

        Returns:
            (list[UUID]): A list of execution IDs of workflows currently awaiting data to be sent to a trigger.
        """
        self.execution_db.session.expire_all()
        wf_statuses = self.execution_db.session.query(WorkflowStatus).filter_by(
            status=WorkflowStatusEnum.awaiting_data).all()
        return [str(wf_status.execution_id) for wf_status in wf_statuses]

    def get_workflow_status(self, execution_id):
        """Gets the current status of a workflow by its execution ID

        Args:
            execution_id (UUID): The execution ID of the workflow

        Returns:
            (int): The status of the workflow
        """
        workflow_status = self.execution_db.session.query(WorkflowStatus).filter_by(execution_id=execution_id).first()
        if workflow_status:
            return workflow_status.status
        else:
            logger.error("Workflow execution id {} does not exist in WorkflowStatus table.").format(execution_id)
            return 0

    def _log_and_send_event(self, event, sender=None, data=None, workflow=None):
        sender = sender or self
        self.results_sender.handle_event(workflow, sender, event=event, data=data)
