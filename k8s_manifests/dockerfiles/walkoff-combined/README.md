WALKOFF is an open-source, flexible, easy to use automation and orchestration framework allowing users to integrate their capabiltiies and cut through the repetitive, tedious tasks slowing them down. For more info, see our GitHub page: https://github.com/nsacyber/WALKOFF.

---

For testing and development purposes, use the image tagged `latest`. The images tagged `appvX` and `workervX` are intended for use in Kubernetes clusters.

---

To use WALKOFF in a single Docker container for development purposes, first create a docker network:

`docker network create --subnet 172.20.0.0/16 walkoffnet0`

Then, pull and run a Redis container and Postgres container:

`docker run --name walkoff-redis --network=walkoffnet0 -d redis`

`docker run --name walkoff-postgres -e POSTGRES_USER=walkoff -e POSTGRES_PASSWORD=walkoff --network walkoffnet0 -d postgres`

You can change the Postgres username and password as you see fit, but ensure you change them consistently in the config below.

Ensure that both containers are running:

`docker ps -a`

Create a file called `walkoff-env.txt` with the following contents:

```
CACHE={"type": "redis", "host": "walkoff-redis", "port": 6379}
HOST=0.0.0.0
PORT=8080
ZMQ_RESULTS_ADDRESS=tcp://0.0.0.0:5556
ZMQ_COMMUNICATION_ADDRESS=tcp://0.0.0.0:5557
WALKOFF_DB_TYPE=postgresql
EXECUTION_DB_TYPE=postgresql
DB_PATH=walkoff
EXECUTION_DB_PATH=execution
WALKOFF_DB_HOST=walkoff-postgres
EXECUTION_DB_HOST=walkoff-postgres
EXECUTION_DB_USERNAME=walkoff
EXECUTION_DB_PASSWORD=walkoff
WALKOFF_DB_USERNAME=walkoff
WALKOFF_DB_PASSWORD=walkoff
SQLALCHEMY_DATABASE_URI=postgresql://walkoff:walkoff@walkoff-postgres/walkoff
```


You can change usernames and passwords as you see fit, but ensure that you change them consistently in all locations. 

This will be passed to your WALKOFF instance as configuration. Ensure that the `host` field in the `CACHE` environment variable matches the name you gave the Redis container you started earlier, as well as the `DB_HOSTNAME` fields matching the Postgres container name.

Then, pull and run the combined WALKOFF container:

`docker run --name walkoff --network=walkoffnet0 --env-file=walkoff-env.txt -p 8080:8080 -d walkoffcyber/walkoff:latest`

Ensure that the WALKOFF container is running:

`docker ps -a`

You can now access the WALKOFF web interface at:

`http://localhost:8080`

If there are any issues, you can check the output of the WALKOFF server with:

`docker logs walkoff`

If you want to start the WALKOFF container with an interactive terminal instead, use these commands: 

`docker run --name walkoff --network=walkoffnet0 --env-file=walkoff-env.txt -p 8080:8080 --entrypoint=/bin/bash -dit walkoffcyber/walkoff:latest`

`docker exec -it walkoff /bin/bash`

`python walkoff.py`

If you wish to copy files into the container (WALKOFF resides in the `/app/walkoff` directory), use a command similar to the following (see docker cp documentation for more details):

`docker cp src.txt walkoff:/app/walkoff/dst.txt`
