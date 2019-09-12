import asyncio, logging, requests, os
import listener.api_gateway_helpers as api
from common.config import config
from minio import Minio
from listener.trigger import Trigger
import time
import threading

logger = logging.getLogger("minio_test")

DELAY = 0.01
REFRESH_DELAY = 1

def setup():
    with requests.session() as s:
        r = api.get_buckets(s)
        buckets = r.json()
        triggers = []

        # Concatinate the trigger sublists generated into a single trigger list
        trig1 = [t for t in [b["triggers"] for b in buckets]]
        for t in trig1:
            triggers += t

        return [Trigger(t["id"], t["event_type"], next((x["name"] for x in buckets if x["id"] == t["parent"]), None), t["prefix"], t["suffix"], t["workflow"])
                for t in triggers]

def listen(trigger):
    event_generator = mc.listen_bucket_notification(trigger.parent, events=[trigger.event_type])
    return event_generator

class EventThread(threading.Thread):
    def __init__(self, trigger):
        super(EventThread, self).__init__()
        self._stop_event = threading.Event()
        self.trigger = trigger

    def stop(self):
        self._stop_event.set()

    def run(self):
        events = listen(self.trigger)
        while not self._stop_event.is_set():
            i = next(events)
            if i:
                with requests.session() as s:
                    workflow_id = self.trigger.workflow
                    r = api.execute_workflow(s, workflow_id)

def main():
    running = []
    runtimes = {}
    while True:
        new_list = setup()
        added = list(set(new_list)-set(running))
        print(added)
        for add in added:
            # runtimes[add.id] = threading.Thread(target=events, args=(add,))
            runtimes[add.id] = EventThread(add)

            runtimes[add.id].start()

            running.append(add)

        #Look for removal
        removed = list(set(running)-set(new_list))
        for r in removed:
            runtimes[add.id].stop()
            del runtimes[r.id]
            running.remove(r)

        print(runtimes)
        time.sleep(REFRESH_DELAY)


if __name__ == "__main__":
    ip = config.MINIO
    access_key = config.get_from_file(config.MINIO_ACCESS_KEY_PATH)
    secret_key = config.get_from_file(config.MINIO_SECRET_KEY_PATH)
    mc = Minio(ip, access_key=access_key, secret_key=secret_key, secure=False)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
    loop.close()