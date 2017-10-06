from core.executionelements.workflow import Workflow
from core.case import callbacks
import logging
import uuid
import threading
from gevent.queue import Queue

logger = logging.getLogger(__name__)

WORKFLOW_RUNNING = 1
WORKFLOW_PAUSED = 2
WORKFLOW_COMPLETED = 4


class WorkflowTask(object):
    def __init__(self, workflow, uid, start, start_input):
        self.workflow = workflow
        self.uid = uid
        self.start = start
        self.start_input = start_input


class SimpleExecutor(object):
    def __init__(self):
        self.pids = []
        self.workflow_status = {}
        self.max_queue_size = 10
        self.queue_timeout = 10
        self.pending_workflows = Queue(maxsize=self.max_queue_size)

        self.worker_thread = None
        self.workflow_thread = None
        self.receiver_thread = None
        self.threading_is_initialized = False
        self.is_shutting_down = False
        self.executing_workflows = {}

    def initialize_threading(self, worker_env=None):
        """Initialize the multiprocessing pool, allowing for parallel execution of workflows.
        Args:
            worker_env (function, optional): Optional alternative worker setup environment function.
        """
        pass

    def shutdown_pool(self, num_workflows=0):
        """Shuts down the threadpool.

        Args:
            num_workflows (int, optional): The number of workflows that should be executed before the pool
                is shutdown.
        """
        pass

    def cleanup_threading(self):
        """Once the threadpool has been shutdown, clear out all of the data structures used in the pool.
        """
        self.pids = []
        self.receiver_thread = None
        self.worker_thread = None

    def worker(self):
        while not self.is_shutting_down:
            task = self.pending_workflows.get()
            self.executing_workflows[task.uid] = task.workflow
            if task.start is not None:
                logger.info('Executing workflow {0} for step {1}'.format(task.workflow.name, task.start))
            else:
                logger.info('Executing workflow {0} with default starting step'.format(task.workflow.name, task.start))
            self.workflow_status[task.uid] = WORKFLOW_RUNNING

            self.workflow_thread = threading.Thread(target=Workflow.execute,
                             args=(task.workflow, task.uid),
                             kwargs={'start': task.start, 'start_input': task.start_input})
            self.workflow_thread.start()
            self.workflow_status[task.uid] = WORKFLOW_RUNNING
            callbacks.SchedulerJobExecuted.send(self)

    def execute_workflow(self, workflow, start=None, start_input=None):
        """Executes a workflow.

        Args:
            start (str, optional): The name of the first, or starting step. Defaults to "start".
            start_input (dict, optional): The input to the starting step of the workflow
        """

        uid = uuid.uuid4().hex
        task = WorkflowTask(workflow, uid, start, start_input)
        self.pending_workflows.put(task, timeout=self.queue_timeout)
        return uid

    def pause_workflow(self, execution_uid, workflow_name):
        """Pauses a workflow that is currently executing.

        Args:
            execution_uid (str): The execution uid of the workflow.
            workflow (Workflow): The workflow to pause.
        """
        if (execution_uid in self.executing_workflows and execution_uid in self.workflow_status
                and self.workflow_status[execution_uid] == WORKFLOW_RUNNING):
            self.workflow_status[execution_uid] = WORKFLOW_PAUSED
            self.executing_workflows[execution_uid].pause()

    def resume_workflow(self, workflow_execution_uid, workflow_name):
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

    def resume_breakpoint_step(self, uid, workflow):
        """Resumes a step that has been specified as a breakpoint.

        Args:
            uid (str): The UID of the workflow that is being executed.
        """
        if workflow and uid in self.workflow_status:
            logger.info('Resuming workflow {0} from breakpoint'.format(workflow.name))
            self.load_balancer.resume_breakpoint_step(uid, workflow.name)
            return True
        else:
            logger.warning('Cannot resume workflow {0} from breakpoint step.'.format(workflow.name))
            return False
