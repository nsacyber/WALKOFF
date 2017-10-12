import logging
import os
import sys
import signal
import gevent
import uuid
import multiprocessing
import threading
import zmq.green as zmq
from core import loadbalancer
from core.threadauthenticator import ThreadAuthenticator
import core.config.config
import core.config.paths
from core.case import callbacks

logger = logging.getLogger(__name__)

WORKFLOW_RUNNING = 1
WORKFLOW_PAUSED = 2
WORKFLOW_COMPLETED = 4

NUM_PROCESSES = core.config.config.num_processes


class MultiprocessedExecutor(object):
    def __init__(self):
        self.threading_is_initialized = False
        self.uid = "executor"
        self.pids = []
        self.workflow_status = {}
        self.workflows_executed = 0

        def handle_workflow_shutdown(sender, **kwargs):
            self.__remove_workflow_status(sender, **kwargs)
        self.handle_data_sent = handle_workflow_shutdown
        callbacks.WorkflowShutdown.connect(handle_workflow_shutdown)

        self.ctx = None
        self.auth = None

        self.load_balancer = None
        self.manager_thread = None
        self.receiver = None
        self.receiver_thread = None

    def __remove_workflow_status(self, sender, **kwargs):
        if sender.get_execution_uid() in self.workflow_status:
            self.workflow_status.pop(sender.get_execution_uid(), None)

    def initialize_threading(self, worker_env=None):
        """Initialize the multiprocessing pool, allowing for parallel execution of workflows.
        Args:
            worker_env (function, optional): Optional alternative worker setup environment function.
        """
        if not (os.path.exists(core.config.paths.zmq_public_keys_path) and
                os.path.exists(core.config.paths.zmq_private_keys_path)):
            logging.error("Certificates are missing - run generate_certificates.py script first.")
            sys.exit(0)

        for i in range(NUM_PROCESSES):
            args = (i,)
            if worker_env:
                args = (i, worker_env,)

            pid = multiprocessing.Process(target=loadbalancer.Worker, args=args)
            pid.start()
            self.pids.append(pid)

        self.ctx = zmq.Context.instance()
        self.auth = ThreadAuthenticator(self.ctx)
        self.auth.start()
        self.auth.allow('127.0.0.1')
        self.auth.configure_curve(domain='*', location=core.config.paths.zmq_public_keys_path)

        self.load_balancer = loadbalancer.LoadBalancer(self.ctx)
        self.receiver = loadbalancer.Receiver(self.ctx)

        self.receiver_thread = threading.Thread(target=self.receiver.receive_results)
        self.receiver_thread.start()

        self.manager_thread = threading.Thread(target=self.load_balancer.manage_workflows)
        self.manager_thread.start()

        self.threading_is_initialized = True
        logger.debug('Controller threading initialized')
        gevent.sleep(0)

    def shutdown_pool(self, num_workflows=0):
        """Shuts down the threadpool.

        Args:
            num_workflows (int, optional): The number of workflows that should be executed before the pool
                is shutdown.
        """
        gevent.sleep(0)

        while True:
            if (num_workflows == 0) or \
                    (num_workflows != 0 and self.receiver is not None
                     and num_workflows == self.receiver.workflows_executed):
                if self.manager_thread:
                    self.load_balancer.thread_exit = True
                    self.manager_thread.join()
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
                    self.receiver_thread.join()
                self.threading_is_initialized = False
                logger.debug('Controller thread pool shutdown')
                break
            gevent.sleep(0.1)
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
        self.load_balancer = None
        self.receiver = None

    def execute_workflow(self, workflow, start=None, start_input=None):
        """Executes a workflow.

        Args:
            start (str, optional): The name of the first, or starting step. Defaults to "start".
            start_input (dict, optional): The input to the starting step of the workflow
        """
        uid = uuid.uuid4().hex

        if not self.threading_is_initialized:
            self.initialize_threading()

        if start is not None:
            logger.info('Executing workflow {0} for step {1}'.format(workflow.name, start))
        else:
            logger.info('Executing workflow {0} with default starting step'.format(workflow.name, start))
        self.workflow_status[uid] = WORKFLOW_RUNNING

        workflow_json = workflow.read()
        if start:
            workflow_json['start'] = start
        if start_input:
            workflow_json['start_input'] = start_input
        workflow_json['execution_uid'] = uid
        self.load_balancer.add_workflow(workflow_json)

        callbacks.SchedulerJobExecuted.send(self)
        # TODO: Find some way to catch a validation error. Maybe pre-validate the input in the controller?
        return uid

    def pause_workflow(self, execution_uid, workflow):
        """Pauses a workflow that is currently executing.

        Args:
            execution_uid (str): The execution uid of the workflow.
            workflow (Workflow): The workflow to pause.
        """
        if (workflow and execution_uid in self.workflow_status
                and self.workflow_status[execution_uid] == WORKFLOW_RUNNING):
            self.load_balancer.pause_workflow(execution_uid, workflow.name)
            self.workflow_status[execution_uid] = WORKFLOW_PAUSED

    def resume_workflow(self, workflow_execution_uid, workflow):
        """Resumes a workflow that has been paused.

        Args:
            workflow_execution_uid (str): The randomly-generated hexadecimal key that was returned from
                pause_workflow(). This is needed to resume a workflow for security purposes.
            workflow (Workflow): The workflow to resume.

        Returns:
            True if successful, false otherwise.
        """
        if workflow:
            if (workflow_execution_uid in self.workflow_status
                    and self.workflow_status[workflow_execution_uid] == WORKFLOW_PAUSED):
                self.load_balancer.resume_workflow(workflow_execution_uid, workflow.name)
                self.workflow_status[workflow_execution_uid] = WORKFLOW_RUNNING
                return True
            else:
                logger.warning('Cannot resume workflow {0}. Invalid key'.format(workflow.name))
                return False

