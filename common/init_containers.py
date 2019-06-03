import json
import time
import os
import multiprocessing

import requests

ES_HOST = os.getenv("ES_HOST", "elasticsearch")
ES_PORT = os.getenv("ES_PORT", "9200")
KIBANA_HOST = os.getenv("KIBANA_HOST", "elasticsearch")
KIBANA_PORT = os.getenv("KIBANA_PORT", "5601")
TIMEOUT = os.getenv("TIMEOUT", "30")


def sint(s, default=None):
    try:
        return int(s)
    except ValueError:
        return default


def is_up(host, port):
    try:
        resp = requests.get(url="http://{}:{}".format(host, port))
        print("{}: {}".format(host, resp))
        if resp.status_code == 200:
            return True
        else:
            return False
    except requests.ConnectionError as e:
        print(repr(e))
        return False


def init_elasticsearch():
    attempts = 0
    while attempts < sint(TIMEOUT, 30):
        if is_up(ES_HOST, ES_PORT):
            try:
                data = {"description": "does post filebeat processing and formatting of bro logs",
                        "processors": [{"date": {"field": "ts", "formats": ["UNIX"], "timezone": "America/New_York"}}]}
                headers = {"Content-Type": "application/json"}
                url = "http://{}:{}/_ingest/pipeline/bro-pipeline".format(ES_HOST, ES_PORT)
                res = requests.put(url=url, data=json.dumps(data), headers=headers)
                if res.status_code == 200:
                    print("Posted to elasticsearch.")
                    return res
            except requests.exceptions.ConnectionError:
                pass
        else:
            print("Attempt: {} to connect to elasticsearch...".format(attempts))
            attempts += 1
            time.sleep(1)
    print("Failed to initialize elasticsearch")


def init_kibana():
    attempts = 0
    while attempts < sint(TIMEOUT, 30):
        if is_up(KIBANA_HOST, KIBANA_PORT):
            headers = {"kbn-xsrf": "true", "Content-Type": "application/json"}
            url = "http://{}:{}/api/saved_objects".format(KIBANA_HOST, KIBANA_PORT)
            try:
                with open("saved_objects.json") as fp:
                    saved_objects = json.load(fp)
                successful_posts = ''
                for obj in saved_objects:
                    obj_url = '/'.join([url, obj["_type"], obj["_id"]])
                    attributes = {"attributes": obj["_source"]}
                    resp = requests.post(url=obj_url, data=json.dumps(attributes), headers=headers)
                    if resp.status_code == 200:
                        successful_posts += obj["_id"] + '\n'
                print("Posted: {} to kibana".format(successful_posts))
                return successful_posts
            except (FileNotFoundError, json.JSONDecodeError) as e:
                print(repr(e))
                return
        else:
            print("Attempt: {} to connect to kibana...".format(attempts))
            attempts += 1
            time.sleep(1)
    print("Failed to initialize elasticsearch")


if __name__ == "__main__":
    es_ps = multiprocessing.Process(target=init_elasticsearch)
    kibana_ps = multiprocessing.Process(target=init_kibana)

    es_ps.start()
    kibana_ps.start()

    es_ps.join()
    kibana_ps.join()

    # init_elasticsearch()
    # init_kibana()