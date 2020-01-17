import docker
import asyncio
from pprint import pprint
import json
import time
import threading

client = docker.from_env()
tasks = []


async def listener():
    for event in client.events():
        e = json.loads(event.decode())
        if e["Type"] == "container" and "walkoff_app" in e["Actor"]["Attributes"]["com.docker.swarm.task.name"]:
            print(e["Actor"]["Attributes"]["com.docker.swarm.task.id"])
        threading.Thread(target=parse_event, args=(e, )).start()


def parse_event(e):
    if e["Type"] == "container" and "walkoff_app" in e["Actor"]["Attributes"]["com.docker.swarm.task.name"]:
        task_id = e["Actor"]["Attributes"]["com.docker.swarm.task.id"]
        service_id = e["Actor"]["Attributes"]["com.docker.swarm.service.id"]

        task = client.services.get(service_id).tasks({"id": task_id})
        if len(task) > 0:
            for t in task:
                status = t["Status"]["Message"]
                if status != "complete" and status != "failed" and status != "shutdown":
                    if task_id not in tasks:
                        tasks.append(task_id)
                        threading.Thread(target=task_listener, args=(status, service_id, task_id,)).start()


def task_listener(status, service_id, task_id):
    while status != "complete" and status != "failed" and status != "shutdown":
        task = client.services.get(service_id).tasks({"id": task_id})
        if len(task) > 0:
            status_code = task[0]["Status"]["ContainerStatus"].get("ExitCode")
            status = task[0]["Status"]["State"]
            pprint(task_id + ": " + status)
            pprint("HEY" + status_code)
            if status_code == 1:
                client.services.get(service_id).remove()

        time.sleep(1)
    else:
        if task_id in tasks:
            tasks.remove(task_id)
        return

# Statuses: NEW, PENDING, ASSIGNED, ACCEPTED, PREPARING, STARTING, RUNNING, COMPLETE, FAILED, SHUTDOWN, REJECTED,
# ORPHANED, REMOVE


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(listener())
