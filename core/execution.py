import multiprocessing as mp
from multiprocessing import Value, Lock

import eventQueue, scheduler
import time
import config

flag = "ok"
mainProcess = None
lock = Lock()
status = Value("i", 0)
queue = eventQueue.eventQueue()
playbook = config.playbook

#Main Processing Loop
def mainLoop(status):
    while status.value == 1:
        #Adds Ready Jobs to EventQueue
        queue.addJobs(scheduler.readyPlays(playbook.plays))

        #Updates the queue
        q = queue.getQueue()

        if len(q) > 0:
            for job in q:
                pq = mp.Queue()
                jobs = []
                for process in range(0, config.executionConfig["maxProcesses"]):
                    if len(q) > 0:
                        #if job in queue execute
                        proc = playbook.getPlay(q.pop())
                        worker = mp.Process(target=proc.executePlay, args=(pq, "start", {"system": None}, ))
                        jobs.append(worker)
                        worker.start()
                for job in jobs:
                    t = pq.get()
                    playbook.getPlay(t["name"]).setLastRun(t["lastRun"])
                    job.join()

        else:
            #If no jobs then sleep for specified amount
            time.sleep(config.executionConfig["secondsDelay"])

    print "SHUTTING DOWN"
    return None

#Starts the Main Processing Loop
def start():
    global mainProcess
    global lock
    global status

    with lock:
        status.value = 1
    mainProcess = mp.Process(target=mainLoop, args=(status, ))
    mainProcess.start()

#Updates the Statuses
def update(sender, **kwargs):
    global mainProcess
    global lock
    global status

    if kwargs["status"] == "start":
        if mainProcess == None:
            start()

    elif kwargs["status"] == "stop":
        if mainProcess is not None:
            with lock:
                status.value = 0
                mainProcess = None
        else:
            print "No Process To Stop!"






