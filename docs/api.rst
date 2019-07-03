.. _api_gateway:

API Gateway
========================

API Endpoints
---------------

apps
''''''''''''''''''''''''''''''''''''''''''''''
.. openapi:: api.yaml
    :paths:
        /apps
        /apps/apis
        /apps/apis/{app}


authorization
''''''''''''''''''''''''''''''''''''''''''''''
.. openapi:: api.yaml
    :paths:
        /auth
        /auth/refresh
        /auth/logout


configuration
''''''''''''''''''''''''''''''''''''''''''''''
.. openapi:: api.yaml
    :paths:
        /configuration


globals
''''''''''''''''''''''''''''''''''''''''''''''
.. openapi:: api.yaml
    :paths:
        /globals
        /globals/{global_var}
        /globals/templates
        /globals/templates/{global_template}


roles
''''''''''''''''''''''''''''''''''''''''''''''
.. openapi:: api.yaml
    :paths:
        /roles
        /roles/{role_id}
        /availableresourceactions


scheduler
''''''''''''''''''''''''''''''''''''''''''''''
.. openapi:: api.yaml
    :paths:
        /scheduler
        /scheduledtasks
        /scheduledtasks/{scheduled_task_id}


users
''''''''''''''''''''''''''''''''''''''''''''''
.. openapi:: api.yaml
    :paths:
        /users
        /users/{user_id}


workflows
''''''''''''''''''''''''''''''''''''''''''''''
.. openapi:: api.yaml
    :paths:
        /workflows
        /workflows/{workflow}


workflowqueue
''''''''''''''''''''''''''''''''''''''''''''''
.. openapi:: api.yaml
    :paths:
        /workflowqueue
        /workflowqueue/{execution}
        /workflowqueue/cleardb


dashboards
''''''''''''''''''''''''''''''''''''''''''''''
.. openapi:: api.yaml
    :paths:
        /dashboards
        /dashboards/{dashboard}


JSON Formulation
------------------
