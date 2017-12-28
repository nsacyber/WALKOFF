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
from walkoff.events import WalkoffEvent
from walkoff.core.multiprocessedexecutor import loadbalancer, worker, threadauthenticator

logger = logging.getLogger(__name__)

WORKFLOW_RUNNING = 1
WORKFLOW_PAUSED = 2
WORKFLOW_COMPLETED = 4
WORKFLOW_AWAITING_DATA = 5


def spawn_worker_processes(worker_environment_setup=None):
    """Initialize the multiprocessing pool, allowing for parallel execution of workflows.

    Args:
        worker_environment_setup (function, optional): Optional alternative worker setup environment function.
    """
    pids = []
    for i in range(walkoff.config.config.num_processes):
        args = (i, worker_environment_setup) if worker_environment_setup else (i,)

        pid = multiprocessing.Process(target=worker.Worker, args=args)
        pid.start()
        pids.append(pid)
    return pids


class MultiprocessedExecutor(object):
    def __init__(self):
        """Initializes a multiprocessed executor, which will handle the execution of workflows.
        """
        self.threading_is_initialized = False
        self.uid = "executor"
        self.pids = None
        self.workflow_status = {}
        self.workflows_executed = 0

        @WalkoffEvent.TriggerActionAwaitingData.connect
        def handle_workflow_wait(sender, **kwargs):
            self.__trigger_workflow_status_wait(sender, **kwargs)

        self.handle_workflow_wait = handle_workflow_wait

        @WalkoffEvent.TriggerActionTaken.connect
        def handle_workflow_continue(sender, **kwargs):
            self.__trigger_workflow_status_continue(sender, **kwargs)

        self.handle_workflow_continue = handle_workflow_continue

        @WalkoffEvent.WorkflowShutdown.connect
        def handle_workflow_shutdown(sender, **kwargs):
            self.__remove_workflow_status(sender, **kwargs)

        self.handle_data_sent = handle_workflow_shutdown

        self.ctx = None
        self.auth = None

        self.manager = None
        self.manager_thread = None
        self.receiver = None
        self.receiver_thread = None

    def __trigger_workflow_status_wait(self, sender, **kwargs):
        self.workflow_status[sender['workflow_execution_uid']] = WORKFLOW_AWAITING_DATA

    def __trigger_workflow_status_continue(self, sender, **kwargs):
        self.workflow_status[sender['workflow_execution_uid']] = WORKFLOW_RUNNING

    def __remove_workflow_status(self, sender, **kwargs):
        if sender['workflow_execution_uid'] in self.workflow_status:
            self.workflow_status.pop(sender['workflow_execution_uid'], None)

    def initialize_threading(self, pids):
        """Initialize the multiprocessing communication threads, allowing for parallel execution of workflows.

        """
        if not (os.path.exists(walkoff.config.paths.zmq_public_keys_path) and
                os.path.exists(walkoff.config.paths.zmq_private_keys_path)):
            logging.error("Certificates are missing - run generate_certificates.py script first.")
            sys.exit(0)
        self.pids = pids
        self.ctx = zmq.Context.instance()
        self.auth = threadauthenticator.ThreadAuthenticator(self.ctx)
        self.auth.start()
        self.auth.allow('127.0.0.1')
        self.auth.configure_curve(domain='*', location=walkoff.config.paths.zmq_public_keys_path)

        self.manager = loadbalancer.LoadBalancer(self.ctx)
        self.receiver = loadbalancer.Receiver(self.ctx)

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

    def execute_workflow(self, workflow, start=None, start_arguments=None):
        """Executes a workflow.

        Args:
            workflow (Workflow): The Workflow to be executed.
            start (str, optional): The name of the first, or starting action. Defaults to None.
            start_arguments (dict, optional): The arguments to the starting action of the workflow. Defaults to None.

        Returns:
            The execution UID of the Workflow.
        """
        uid = str(uuid.uuid4())

        if start is not None:
            logger.info('Executing workflow {0} for action {1}'.format(workflow.name, start))
        else:
            logger.info('Executing workflow {0} with default starting action'.format(workflow.name, start))
        self.workflow_status[uid] = WORKFLOW_RUNNING

        workflow_json = workflow.read()
        if start:
            workflow_json['start'] = start
        if start_arguments:
            workflow_json['start_arguments'] = start_arguments
        workflow_json['execution_uid'] = uid
        self.manager.add_workflow(workflow_json)

        WalkoffEvent.SchedulerJobExecuted.send(self)
        # TODO: Find some way to catch a validation error. Maybe pre-validate the argument in the controller?
        return uid

    def pause_workflow(self, execution_uid):
        """Pauses a workflow that is currently executing.

        Args:
            execution_uid (str): The execution uid of the workflow.
        """
        if (execution_uid in self.workflow_status
            and self.workflow_status[execution_uid] == WORKFLOW_RUNNING):
            self.manager.pause_workflow(execution_uid)
            self.workflow_status[execution_uid] = WORKFLOW_PAUSED
            return True
        else:
            logger.warning('Cannot pause workflow {0}. Invalid key'.format(execution_uid))
            return False

    def resume_workflow(self, workflow_execution_uid):
        """Resumes a workflow that has been paused.

        Args:
            workflow_execution_uid (str): The randomly-generated hexadecimal key that was returned from
                pause_workflow(). This is needed to resume a workflow for security purposes.

        Returns:
            True if successful, false otherwise.
        """
        if (workflow_execution_uid in self.workflow_status
            and self.workflow_status[workflow_execution_uid] == WORKFLOW_PAUSED):
            self.manager.resume_workflow(workflow_execution_uid)
            self.workflow_status[workflow_execution_uid] = WORKFLOW_RUNNING
            return True
        else:
            logger.warning('Cannot resume workflow {0}. Invalid key'.format(workflow_execution_uid))
            return False

    def get_waiting_workflows(self):
        """Gets a list of the execution UIDs of workflows currently awaiting data to be sent to a trigger.

        Returns:
            A list of execution UIDs of workflows currently awaiting data to be sent to a trigger.
        """
        return [uid for uid, status in self.workflow_status.items() if status == WORKFLOW_AWAITING_DATA]

    def get_workflow_status(self, workflow_execution_uid):
        """Gets the current status of a workflow by its execution UID

        Args:
            workflow_execution_uid (str): The execution UID of the workflow

        Returns:
            The status of the workflow
        """
        try:
            return self.workflow_status[workflow_execution_uid]
        except KeyError:
            logger.error("Key {} does not exist in {}.").format(workflow_execution_uid, self.workflow_status.items())
            return 0

    def send_data_to_trigger(self, data_in, workflow_uids, arguments=None):
        """Sends the data_in to the workflows specified in workflow_uids.

        Args:
            data_in (dict): Data to be used to match against the triggers for an Action awaiting data.
            workflow_uids (list[str]): A list of workflow execution UIDs to send this data to.
            arguments (list[Argument]): An optional list of Arguments to update for an Action awaiting data for a trigger.
                Defaults to None.
        """
        arguments = arguments if arguments is not None else []
        self.manager.send_data_to_trigger(data_in, workflow_uids, arguments)
