import argparse
import multiprocessing
import os
import signal
import time

import walkoff.config
from walkoff.multiprocessedexecutor.worker import Worker


def parse_args():
    parser = argparse.ArgumentParser(description='Script to start WALKOFF Workflow workers')
    parser.add_argument('-n', '--num', help='Number of workers to spawn')
    parser.add_argument('-v', '--version', help='Get the version of WALKOFF running', action='store_true')
    parser.add_argument('-c', '--config', help='Configuration file to use')
    args = parser.parse_args()
    if args.version:
        print(walkoff.__version__)
        exit(0)

    return args


def spawn_worker_processes(num_processes, config):
    """Initialize the multiprocessing pool, allowing for parallel execution of workflows.
    """
    pids = []
    try:
        for i in range(num_processes):
            pid = multiprocessing.Process(target=Worker, args=(i, config.CONFIG_PATH))
            print('Starting worker process {}'.format(i))
            pid.start()
            pids.append(pid)
        return pids
    except KeyboardInterrupt:
        shutdown_procs(pids)


def shutdown_procs(procs):
    for proc in procs:
        if proc.is_alive():
            print('Shutting down process {}'.format(proc.pid))
            os.kill(proc.pid, signal.SIGABRT)
            proc.join(timeout=3)
            try:
                os.kill(proc.pid, signal.SIGKILL)
            except (OSError, AttributeError):
                pass


if __name__ == '__main__':
    args = parse_args()
    num_procs = walkoff.config.Config.NUMBER_PROCESSES
    if args.config:
        walkoff.config.Config.load_config(args.config)
        num_procs = walkoff.config.Config.NUMBER_PROCESSES
    if args.num:
        num_procs = args.num

    processes = spawn_worker_processes(num_procs, walkoff.config.Config)

    try:
        while True:
            time.sleep(100)
    except KeyboardInterrupt:
        shutdown_procs(processes)
    finally:
        os._exit(0)
