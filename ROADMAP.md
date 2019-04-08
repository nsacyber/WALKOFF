WALKOFF 1.0.0 is intended to present a more robust and scalable implementation of Apps and Workers.

This alpha is **not feature complete and is not production-ready**, but is intended for interested parties to test the 
new architecture and provide feedback.

### 1.0 Intentions

- Designed to run inside Docker Compose or Docker Swarm.
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

For the alpha release, here are some of the areas of interest we would like feedback on:

- First-time app development.
- Stress-testing of large/branching workflows.
- Anything you can manage to break.

### Roadmap:

The following section gives a rough approximation of what we are looking to accomplish in upcoming releases.

#### 1.0.0-alpha.1

- Core components functioning under new architecture.
- Stable enough to begin writing usable apps and workflows

#### 1.0.0-beta.1

- Functional feature parity with pre-1.0 WALKOFF intentions
    - Event-driven actions (removed in 0.5.0)
    - Triggers (removed in 1.0.0-alpha.1)
- Support for more complex workflow composition
    - Nested workflows (running a workflow as a node in another workflow)
    - Parallelized actions (dividing up work for a node into n subnodes)

#### 1.0.0-rc.1:

- Completed unit testing of components and end-to-end testing of a running cluster.
- Security hardening.
- "Essentials" app suite, e.g. SSH, PowerShell, other common utilities.
