import urllib3

import walkoff_client as walkoff


class WalkoffAPI:

    def __init__(self, host, username, password):
        # Create a config that represents our Walkoff server
        self.config = walkoff.Configuration()
        self.config.host = host

        # Since Walkoff uses a self-signed certificate, we need to disable certificate verification
        self.config.verify_ssl = False
        self.config.ssl_ca_cert = None
        self.config.assert_hostname = False
        self.config.cert_file = None
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        # Create a base API client with which you will interact with Walkoff
        self.api_client = walkoff.ApiClient(configuration=self.config)

        # Create an authentication API client and log in
        self.auth_api = walkoff.AuthorizationApi(self.api_client)
        self.creds = walkoff.Authentication(username=username, password=password)
        self.tokens = self.auth_api.login(self.creds)
        self.config.access_token = self.tokens.access_token

    def reauth(self):
        self.tokens = self.auth_api.login(self.creds)
        self.config.access_token = self.tokens.access_token

    def execute_workflow(self, workflow_id, parameters=None, workflow_variables=None):
        self.reauth()

        # Create a workflow API client and perform your desired actions
        workflow_api = walkoff.WorkflowsApi(self.api_client)
        workflow = workflow_api.read_workflow(workflow_id)
        print(workflow)

        new_params = []
        if parameters:
            for action in workflow.actions:
                if action.id_ == workflow.start:
                    existing_parameters_by_name = {p.name: p for p in action.parameters}
                    for name, value in parameters.items():
                        existing_parameters_by_name[name].value = value
                    new_params = list(existing_parameters_by_name.values())


        if workflow_variables:
            for wf in workflow.workflow_variables:
                wf.value = workflow_variables[wf.name]

        wfq_api = walkoff.WorkflowQueueApi(self.api_client)
        wfq_exec = walkoff.ExecuteWorkflow(workflow_id=workflow.id_,
                                           parameters=new_params,
                                           workflow_variables=workflow.workflow_variables)

        r = wfq_api.execute_workflow(wfq_exec)
        print(r)

if __name__ == "__main__":
    w = WalkoffAPI("https://localhost:8080/api", "admin", "admin")
    w.execute_workflow("Test", {"targets": ["127.0.0.1"], "options": "-sS -T4"})
