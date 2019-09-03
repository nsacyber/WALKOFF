WALKOFF 1.0.0 is intended to present a more robust and scalable implementation of Apps and Workers.

The aim of this beta is to finish building out features intended to make running WALKOFF in production smoother.  

### 1.0 Intentions

- Designed to run with Docker Swarm.
    - This eliminates all installation dependencies other than Docker and Docker Compose 
    - Each component can also be run outside of a Docker container for development or debug, as long as it has 
    connectivity to the other pieces. However this is not the supported method of installation.
- Concurrent action execution and replicated app containers:
    - In 0.9.4, work was distributed up to the workflow level - worker containers could be replicated, and workflows 
    would be load-balanced between them. However, workflows were still serially executed within those workers.
    - In 1.0.0, work is now distributed at the action level to replicated containers for each app. The workers 
    perform a breadth-first search and schedule actions once they are ready to execute, and multiple actions in a 
    workflow can run concurrently and asynchronously. This should provide a much more scalable solution for executing
    actions.
        - This also means that the containerized apps could be written in languages other than Python, as long as they 
        can communicate with the rest of WALKOFF through Redis.

### Testing & Feedback Areas of Interest

For the beta release, here are some of the areas of interest we would like feedback on:

- App development through the App Editor page.
- Stress-testing of large/branching workflows and large numbers of concurrent workflows.
- Testing of scaling WALKOFF across multiple Docker Swarm nodes.

### Roadmap:

The following section gives a rough approximation of what we are looking to accomplish in the leadup to a full 1.0.0 release.

#### 1.0.0-alpha.1

- Core components functioning under new architecture.
- Stable enough to begin writing usable apps and workflows.
- "Essentials" app suite, e.g. SSH, PowerShell, other common utilities.
- All workflow node types (Actions, Parallel Actions, Conditions, Transforms, Triggers).

#### 1.0.0-beta.1

- App Editor for modifying apps on the UI.
- Bootloader for automating deployment of WALKOFF.
- Further stability improvements.

#### 1.0.0-rc.1 **(Next Step)**:

- Security hardening.
- Complete unit testing of components (maybe) and end-to-end testing of a running cluster.
- Validation of WALKOFF running and scaling to large production workloads on multiple Docker Swarm nodes.
- Dashboards for monitoring and working with WALKOFF outside of Docker CLI
- Resource-aware scaling of apps and workflows.
- API Gateway transitioned to FastAPI async framework.
- Worker self-healing and error correction to prevent stale work or hangups.

#### 1.1.0:

- Future plans include features such as building App SDKs for other languages, building out more ways of executing workflows (e.g. pollers and listeners)
