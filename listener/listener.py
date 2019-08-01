import asyncio, logging, requests, os
import api_gateway_helpers as api
from minio import Minio


import uuid

logger = logging.getLogger("minio_test")

DELAY = 0.01
class Listener():
    def __init__(self):
        self.buckets = []
        self._setup()

    def _setup(self):
        with requests.session() as s:
            r = api.get_buckets(s)
            self.buckets = r.json()

            for bn in range(0, len(self.buckets)):
                b = self.buckets[bn]["triggers"]
                for tn in range(0, len(b)):
                    r = api.get_workflow(s, b[tn]["workflow"])

                    workflow_json = r.json()
                    self.buckets[bn]["triggers"][tn]["workflow_raw"] = workflow_json

def listen(bucket):
    event_generator = mc.listen_bucket_notification(bucket["name"], events=[t["event_type"] for t in bucket["triggers"]])
    return event_generator

#Creates an async generator
async def coroutine_read_events(evts):
    for evt in evts:
        yield evt
        await asyncio.sleep(DELAY)

#Reads the async generator
async def events(bucket, b):
    async for i in coroutine_read_events(b):
        with requests.session() as s:
            workflow_id = bucket["triggers"][0]["workflow"]
            r = api.execute_workflow(s, workflow_id)
            print(r.text)

async def main(buckets):
    evts = [asyncio.Task(events(b, listen(b))) for b in buckets]
    await asyncio.gather(*evts)

if __name__ == "__main__":
    ip = os.getenv("MINIO_IP")
    access_key = os.getenv("MINIO_ACCESS_KEY")
    secret_key = os.getenv("MINIO_SECRET_KEY")
    mc = Minio(ip, access_key=access_key, secret_key=secret_key, secure=False)
    l = Listener()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(l.buckets))