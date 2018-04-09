import logging
import multiprocessing
import os
import signal
import sys
import threading
import uuid

import gevent
import zmq.green as zmq

from walkoff.executiondb import ExecutionDatabase
from walkoff.events import WalkoffEvent
from walkoff.executiondb import WorkflowStatusEnum
from walkoff.executiondb.saved_workflow import SavedWorkflow
from walkoff.executiondb.workflow import Workflow
from walkoff.executiondb.workflowresults import WorkflowStatus
from walkoff.multiprocessedexecutor.workflowexecutioncontroller import WorkflowExecutionController, Receiver
from walkoff.multiprocessedexecutor.threadauthenticator import ThreadAuthenticator
from walkoff.multiprocessedexecutor.worker import Worker
from flask import current_app
logger = logging.getLogger(__name__)


def spawn_worker_processes(number_processes, num_threads_per_process, zmq_private_keys_path, zmq_results_address,
                           zmq_communication_address, worker_environment_setup=None):
    """Initialize the multiprocessing pool, allowing for parallel execution of workflows.

    Args:
        number_processes (int): The number of processes to spawn
        num_threads_per_process (int): The number of threads per process to spawn
        zmq_private_keys_path (str): The path to the ZMQ private keys
        zmq_results_address (str): The address of the ZMQ results socket
        zmq_communication_address (str): The address of the ZMQ comm socket
        worker_environment_setup (function, optional): Optional alternative worker setup environment function.
    """
    pids = []
    for i in range(number_processes):
        args = (i, num_threads_per_process, zmq_private_keys_path, zmq_results_address, zmq_communication_address,
                worker_environment_setup) if worker_environment_setup else (i, num_threads_per_process,
                                                                            zmq_private_keys_path, zmq_results_address,
                                                                            zmq_communication_address)
        pid = multiprocessing.Process(target=Worker, args=args)
        pid.start()
        pids.append(pid)
    return pids


class MultiprocessedExecutor(object):
    def __init__(self, cache, event_logger):
        """Initializes a multiprocessed executor, which will handle the execution of workflows.
        """
        self.threading_is_initialized = False
        self.id = "controller"
        self.pids = None
        self.workflows_executed = 0

        self.ctx = None  # TODO: Test if you can always use the singleton
        self.auth = None

        self.manager = None
        self.receiver = None
        self.receiver_thread = None
        self.cache = cache
        self.event_logger = event_logger
        
        self.execution_db = ExecutionDatabase.instance

    def initialize_threading(self, zmq_public_keys_path, zmq_private_keys_path, zmq_results_address,
                             zmq_communication_address, app, pids=None):
        """Initialize the multiprocessing communication threads, allowing for parallel execution of workflows.

        Args:
            zmq_public_keys_path (str): The path to the ZMQ public keys.
            zmq_private_keys_path (str): The path to the ZMQ private keys.
            zmq_results_address (str): The address of the ZMQ results socket
            zmq_communication_address (str): The address of the ZMQ comm socket
            pids (list, optional): Optional list of spawned processes. Defaults to None

        """
        if not (os.path.exists(zmq_public_keys_path) and
                os.path.exists(zmq_private_keys_path)):
            logging.error("Certificates are missing - run generate_certificates.py script first.")
            sys.exit(0)
        self.pids = pids
        self.ctx = zmq.Context.instance()
        self.auth = ThreadAuthenticator()
        self.auth.start()
        self.auth.allow('127.0.0.1')
        self.auth.configure_curve(domain='*', location=zmq_public_keys_path)

        self.manager = WorkflowExecutionController(self.cache, zmq_private_keys_path, zmq_communication_address)
        self.receiver = Receiver(zmq_private_keys_path, zmq_results_address, app)

        self.receiver_thread = threading.Thread(target=self.receiver.receive_results)
        self.receiver_thread.start()

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
        assert(num_workflows == self.receiver.workflows_executed)
        self.receiver.workflows_executed = 0

    def shutdown_pool(self):
        """Shuts down the threadpool.
        """
        self.manager.send_exit_to_worker_comms()
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
        workflow = self.execution_db.session.query(Workflow).filter_by(id=workflow_id).first()
        if not workflow:
            logger.error('Attempted to execute workflow which does not exist')
            return None, 'Attempted to execute workflow which does not exist'

        execution_id = execution_id_in if execution_id_in else str(uuid.uuid4())

        if start is not None:
            logger.info('Executing workflow {0} for action {1}'.format(workflow.name, start))
        else:
            logger.info('Executing workflow {0} with default starting action'.format(workflow.name, start))

        workflow_data = {'execution_id': execution_id, 'id': str(workflow.id), 'name': workflow.name}
        self._log_and_send_event(WalkoffEvent.WorkflowExecutionPending, sender=workflow_data)
        self.manager.add_workflow(workflow.id, execution_id, start, start_arguments, resume)

        self._log_and_send_event(WalkoffEvent.SchedulerJobExecuted)
        return execution_id

    def pause_workflow(self, execution_id):
        """Pauses a workflow that is currently executing.

        Args:
            execution_id (str): The execution id of the workflow.
        """
        workflow_status = self.execution_db.session.query(WorkflowStatus).filter_by(
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
        workflow_status = self.execution_db.session.query(WorkflowStatus).filter_by(
            execution_id=execution_id).first()

        if workflow_status and workflow_status.status == WorkflowStatusEnum.paused:
            saved_state = self.execution_db.session.query(SavedWorkflow).filter_by(
                workflow_execution_id=execution_id).first()
            workflow = self.execution_db.session.query(Workflow).filter_by(
                id=workflow_status.workflow_id).first()
            workflow._execution_id = execution_id
            self._log_and_send_event(WalkoffEvent.WorkflowResumed, sender=workflow)

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
        workflow_status = self.execution_db.session.query(WorkflowStatus).filter_by(
            execution_id=execution_id).first()

        if workflow_status:
            if workflow_status.status in [WorkflowStatusEnum.pending, WorkflowStatusEnum.paused,
                                          WorkflowStatusEnum.awaiting_data]:
                workflow = self.execution_db.session.query(Workflow).filter_by(
                    id=workflow_status.workflow_id).first()
                if workflow is not None:
                    self._log_and_send_event(
                        WalkoffEvent.WorkflowAborted,
                        sender={'execution_id': execution_id, 'id': workflow_status.workflow_id, 'name': workflow.name})
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
        saved_state = self.execution_db.session.query(SavedWorkflow).filter_by(
            workflow_execution_id=execution_id).first()
        workflow = self.execution_db.session.query(Workflow).filter_by(
            id=saved_state.workflow_id).first()
        workflow._execution_id = execution_id

        executed = False
        exec_action = None
        for action in workflow.actions:
            if action.id == saved_state.action_id:
                exec_action = action
                executed = action.execute_trigger(data_in, saved_state.accumulator)
                break

        if executed:
            self._log_and_send_event(
                WalkoffEvent.TriggerActionTaken,
                sender=exec_action,
                data={'workflow_execution_id': execution_id})
            self.execute_workflow(
                workflow.id,
                execution_id_in=execution_id,
                start=str(saved_state.action_id),
                start_arguments=arguments,
                resume=True)
            return True
        else:
            self._log_and_send_event(
                WalkoffEvent.TriggerActionNotTaken,
                sender=exec_action,
                data={'workflow_execution_id': execution_id})
            return False

    def get_waiting_workflows(self):
        """Gets a list of the execution IDs of workflows currently awaiting data to be sent to a trigger.

        Returns:
            A list of execution IDs of workflows currently awaiting data to be sent to a trigger.
        """
        self.execution_db.session.expire_all()
        wf_statuses = self.execution_db.session.query(WorkflowStatus).filter_by(
            status=WorkflowStatusEnum.awaiting_data).all()
        return [str(wf_status.execution_id) for wf_status in wf_statuses]

    def get_workflow_status(self, execution_id):
        """Gets the current status of a workflow by its execution ID

        Args:
            execution_id (str): The execution ID of the workflow

        Returns:
            The status of the workflow
        """
        workflow_status = self.execution_db.session.query(WorkflowStatus).filter_by(
            execution_id=execution_id).first()
        if workflow_status:
            return workflow_status.status
        else:
            logger.error("Key {} does not exist in database.").format(execution_id)
            return 0

    def _log_and_send_event(self, event, sender=None, data=None):
        sender = sender or self
        sender_id = sender.id if not isinstance(sender, dict) else sender['id']
        self.event_logger.log(event, sender_id, data=data)
        event.send(sender, data=data)

    def create_case(self, case_id, subscriptions):
        self.manager.create_case(case_id, subscriptions)

    def update_case(self, case_id, subscriptions):
        self.manager.create_case(case_id, subscriptions)

    def delete_case(self, case_id):
        self.manager.delete_case(case_id)
