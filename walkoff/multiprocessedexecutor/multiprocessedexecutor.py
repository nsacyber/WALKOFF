import logging
import multiprocessing
import os
import signal
import sys
import threading
import uuid

import gevent
import zmq.green as zmq

import walkoff.config.config
import walkoff.config.paths
from walkoff import executiondb
from walkoff.events import WalkoffEvent
from walkoff.multiprocessedexecutor.loadbalancer import LoadBalancer, Receiver
from walkoff.multiprocessedexecutor.worker import Worker
from walkoff.multiprocessedexecutor.threadauthenticator import ThreadAuthenticator
from walkoff.executiondb.workflow import Workflow
from walkoff.executiondb.workflowresults import WorkflowStatus
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.executiondb import WorkflowStatusEnum

logger = logging.getLogger(__name__)


def spawn_worker_processes(worker_environment_setup=None):
    """Initialize the multiprocessing pool, allowing for parallel execution of workflows.

    Args:
        worker_environment_setup (function, optional): Optional alternative worker setup environment function.
    """
    pids = []
    for i in range(walkoff.config.config.num_processes):
        args = (i, worker_environment_setup) if worker_environment_setup else (i,)

        pid = multiprocessing.Process(target=Worker, args=args)
        pid.start()
        pids.append(pid)
    return pids


class MultiprocessedExecutor(object):
    def __init__(self):
        """Initializes a multiprocessed executor, which will handle the execution of workflows.
        """
        self.threading_is_initialized = False
        self.id = "controller"
        self.pids = None
        self.workflows_executed = 0

        self.ctx = None
        self.auth = None

        self.manager = None
        self.manager_thread = None
        self.receiver = None
        self.receiver_thread = None

    def initialize_threading(self, pids=None):
        """Initialize the multiprocessing communication threads, allowing for parallel execution of workflows.

        """
        if not (os.path.exists(walkoff.config.paths.zmq_public_keys_path) and
                os.path.exists(walkoff.config.paths.zmq_private_keys_path)):
            logging.error("Certificates are missing - run generate_certificates.py script first.")
            sys.exit(0)
        self.pids = pids
        self.ctx = zmq.Context.instance()
        self.auth = ThreadAuthenticator(self.ctx)
        self.auth.start()
        self.auth.allow('127.0.0.1')
        self.auth.configure_curve(domain='*', location=walkoff.config.paths.zmq_public_keys_path)

        self.manager = LoadBalancer(self.ctx)
        self.receiver = Receiver(self.ctx)

        self.receiver_thread = threading.Thread(target=self.receiver.receive_results)
        self.receiver_thread.start()

        self.manager_thread = threading.Thread(target=self.manager.manage_workflows)
        self.manager_thread.start()

        self.threading_is_initialized = True
        logger.debug('Controller threading initialized')

    def wait_and_reset(self, num_workflows):
        timeout = 0
        shutdown = 10

        while timeout < shutdown:
            if self.receiver is not None and num_workflows == self.receiver.workflows_executed:
                break
            timeout += 0.1
            gevent.sleep(0.1)
        self.receiver.workflows_executed = 0

    def shutdown_pool(self):
        """Shuts down the threadpool.
        """
        self.manager.send_exit_to_worker_comms()
        if self.manager_thread:
            self.manager.thread_exit = True
            self.manager_thread.join(timeout=1)
        if len(self.pids) > 0:
            for p in self.pids:
                if p.is_alive():
                    os.kill(p.pid, signal.SIGABRT)
                    p.join(timeout=3)
                    try:
                        os.kill(p.pid, signal.SIGKILL)
                    except (OSError, AttributeError):
                        pass
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
        return

    def cleanup_threading(self):
        """Once the threadpool has been shutdown, clear out all of the data structures used in the pool.
        """
        self.pids = []
        self.receiver_thread = None
        self.manager_thread = None
        self.workflows_executed = 0
        self.threading_is_initialized = False
        self.manager = None
        self.receiver = None

    def execute_workflow(self, workflow_id, execution_id_in=None, start=None, start_arguments=None, resume=False):
        """Executes a workflow.

        Args:
            workflow_id (Workflow): The Workflow to be executed.
            execution_id_in (str, optional): The optional execution ID to provide for the workflow. Should only be
                used (and is required) when resuming a workflow. Must be valid UUID4. Defaults to None.
            start (str, optional): The ID of the first, or starting action. Defaults to None.
            start_arguments (list[Argument]): The arguments to the starting action of the workflow. Defaults to None.
            resume (bool, optional): Optional boolean to resume a previously paused workflow. Defaults to False.

        Returns:
            The execution ID of the Workflow.
        """
        workflow = executiondb.execution_db.session.query(Workflow).filter_by(id=workflow_id).first()
        if not workflow:
            logger.error('Attempted to execute workflow which does not exist')
            return None, 'Attempted to execute workflow which does not exist'

        execution_id = execution_id_in if execution_id_in else str(uuid.uuid4())

        if start is not None:
            logger.info('Executing workflow {0} for action {1}'.format(workflow.name, start))
        else:
            logger.info('Executing workflow {0} with default starting action'.format(workflow.name, start))

        workflow_data = {'execution_id': execution_id, 'id': workflow.id, 'name': workflow.name}
        WalkoffEvent.WorkflowExecutionPending.send(workflow_data)
        self.manager.add_workflow(workflow.id, execution_id, start, start_arguments, resume)

        WalkoffEvent.SchedulerJobExecuted.send(self)
        return execution_id

    def pause_workflow(self, execution_id):
        """Pauses a workflow that is currently executing.

        Args:
            execution_id (str): The execution id of the workflow.
        """
        workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
            execution_id=execution_id).first()
        if workflow_status and workflow_status.status == WorkflowStatusEnum.running:
            self.manager.pause_workflow(execution_id)
            return True
        else:
            logger.warning('Cannot pause workflow {0}. Invalid key, or workflow not running.'.format(execution_id))
            return False

    def resume_workflow(self, execution_id):
        """Resumes a workflow that is currently paused.

        Args:
            execution_id (str): The execution id of the workflow.
        """
        workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
            execution_id=execution_id).first()

        if workflow_status and workflow_status.status == WorkflowStatusEnum.paused:
            saved_state = executiondb.execution_db.session.query(SavedWorkflow).filter_by(
                workflow_execution_id=execution_id).first()
            workflow = executiondb.execution_db.session.query(Workflow).filter_by(
                id=workflow_status.workflow_id).first()
            workflow._execution_id = execution_id
            WalkoffEvent.WorkflowResumed.send(workflow)

            start = saved_state.action_id if saved_state else workflow.start
            self.execute_workflow(workflow.id, execution_id_in=execution_id, start=start, resume=True)
            return True
        else:
            logger.warning('Cannot resume workflow {0}. Invalid key, or workflow not paused.'.format(execution_id))
            return False

    def abort_workflow(self, execution_id):
        """Abort a workflow.

        Args:
            execution_id (str): The execution id of the workflow.
        """
        workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
            execution_id=execution_id).first()

        if workflow_status:
            if workflow_status.status in [WorkflowStatusEnum.pending, WorkflowStatusEnum.paused,
                                          WorkflowStatusEnum.awaiting_data]:
                workflow = walkoff.coredb.devicedb.device_db.session.query(Workflow).filter_by(
                    id=workflow_status.workflow_id).first()
                if workflow is not None:
                    WalkoffEvent.WorkflowAborted.send({'execution_id': execution_id, 'id': workflow_status.workflow_id, 'name': workflow.name})
            elif workflow_status.status == WorkflowStatusEnum.running:
                self.manager.abort_workflow(execution_id)
            return True
        else:
            logger.warning(
                'Cannot resume workflow {0}. Invalid key, or workflow already shutdown.'.format(execution_id))
            return False

    def resume_trigger_step(self, execution_id, data_in, arguments=None):
        """Resumes a workflow awaiting trigger data, if the conditions are met.

        Args:
            execution_id (str): The execution ID of the workflow
            data_in (dict): The data to send to the trigger
            arguments (list[Argument], optional): Optional list of new Arguments for the trigger action.
                Defaults to None.
        """
        saved_state = executiondb.execution_db.session.query(SavedWorkflow).filter_by(
            workflow_execution_id=execution_id).first()
        workflow = executiondb.execution_db.session.query(Workflow).filter_by(
            id=saved_state.workflow_id).first()
        workflow._execution_id = execution_id

        executed = False
        exec_action = None
        for action in workflow.actions.values():
            if action.id == saved_state.action_id:
                exec_action = action
                executed = action.execute_trigger(data_in, saved_state.accumulator)
                break

        if executed:
            WalkoffEvent.TriggerActionTaken.send(exec_action, data={'workflow_execution_id': execution_id})
            self.execute_workflow(workflow.id, execution_id_in=execution_id, start=saved_state.action_id,
                                  start_arguments=arguments, resume=True)
            return True
        else:
            WalkoffEvent.TriggerActionNotTaken.send(exec_action, data={'workflow_execution_id': execution_id})
            return False

    @staticmethod
    def get_waiting_workflows():
        """Gets a list of the execution IDs of workflows currently awaiting data to be sent to a trigger.

        Returns:
            A list of execution IDs of workflows currently awaiting data to be sent to a trigger.
        """
        executiondb.execution_db.session.expire_all()
        wf_statuses = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
            status=WorkflowStatusEnum.awaiting_data).all()
        return [str(wf_status.execution_id) for wf_status in wf_statuses]

    def get_workflow_status(self, execution_id):
        """Gets the current status of a workflow by its execution ID

        Args:
            execution_id (str): The execution ID of the workflow

        Returns:
            The status of the workflow
        """
        workflow_status = executiondb.execution_db.session.query(WorkflowStatus).filter_by(
            execution_id=execution_id).first()
        if workflow_status:
            return workflow_status.status
        else:
            logger.error("Key {} does not exist in database.").format(execution_id)
            return 0


multiprocessedexecutor = MultiprocessedExecutor()
