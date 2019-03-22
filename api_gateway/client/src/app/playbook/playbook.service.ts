import { Injectable } from '@angular/core';
import { plainToClass, classToPlain } from 'class-transformer';
import { HttpClient } from '@angular/common/http';

import { Workflow } from '../models/playbook/workflow';
import { Playbook } from '../models/playbook/playbook';
import { AppApi } from '../models/api/appApi';
import { Global } from '../models/global';
import { Variable } from '../models/variable';
import { User } from '../models/user';
import { Role } from '../models/role';
import { WorkflowStatus } from '../models/execution/workflowStatus';

import { GlobalsService } from '../globals/globals.service';
import { ExecutionService } from '../execution/execution.service';
import { SettingsService } from '../settings/settings.service';
import { UtilitiesService } from '../utilities.service';

import { UUID } from 'angular2-uuid';

import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/catch';
import 'rxjs/add/operator/map';

@Injectable({
	providedIn: 'root'
})
export class PlaybookService {
	constructor(private http: HttpClient, private utils: UtilitiesService, private executionService: ExecutionService,
				private globalsService: GlobalsService, private settingsService: SettingsService) {}

	/**
	 * Returns all playbooks and their child workflows in minimal form (id, name).
	 */
	getPlaybooks(): Promise<Playbook[]> {
		return this.http.get('/api/playbooks')
			.toPromise()
			.then((data) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Saves a new playbook.
	 * @param playbook New playbook to be saved
	 */
	newPlaybook(playbook: Playbook): Promise<Playbook> {
		return this.http.post('/api/playbooks', classToPlain(playbook))
			.toPromise()
			.then((data) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Renames an existing playbook.
	 * @param playbookId Current playbook ID to change
	 * @param newName New name for the updated playbook
	 */
	renamePlaybook(playbookId: string, newName: string): Promise<Playbook> {
		return this.http.patch('/api/playbooks', { id: playbookId, name: newName })
			.toPromise()
			.then((data: object) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Duplicates and saves an existing playbook, it's workflows, actions, branches, etc. under a new name.
	 * @param playbookId ID of the playbook to duplicate
	 * @param newName Name of the new copy to be saved
	 */
	duplicatePlaybook(playbookId: string, newName: string): Promise<Playbook> {
		return this.http.post(`/api/playbooks?source=${playbookId}`, { name: newName })
			.toPromise()
			.then((data) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Deletes a playbook by name.
	 * @param playbookIdToDelete ID of playbook to be deleted.
	 */
	deletePlaybook(playbookIdToDelete: string): Promise<void> {
		return this.http.delete(`/api/playbooks/${playbookIdToDelete}`)
			.toPromise()
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Exports a playbook as an Observable (component handles the actual 'save').
	 * @param playbookId: ID of playbook to export
	 */
	exportPlaybook(playbookId: string): Observable<Blob> {
		return this.http.get(`/api/playbooks/${playbookId}?mode=export`, { responseType: 'blob' })
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Imports a playbook from a supplied file.
	 * @param fileToImport File to be imported
	 */
	importPlaybook(fileToImport: File): Observable<Playbook> {
		const formData: FormData = new FormData();
		formData.append('file', fileToImport, fileToImport.name);

		const headers = { 'Accept': 'application/json' }

		return this.http.post('/api/playbooks', formData, { headers })
			.map(res => plainToClass(Playbook, res))
			.catch(error => Observable.throw(error));
	}

	/**
	 * Returns all playbooks and their child workflows in minimal form (id, name).
	 */
	getWorkflows(): Promise<Workflow[]> {
		return this.http.get('/api/workflows')
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Duplicates a workflow under a given playbook, it's actions, branches, etc. under a new name.
	 * @param sourceWorkflowId Current workflow ID to be duplicated
	 * @param destinationPlaybookId ID of playbook the workflow will be duplicated to
	 * @param newName Name for the new copy to be saved
	 */
	duplicateWorkflow(
		sourceWorkflowId: string, newName: string,
	): Promise<Workflow> {
		return this.http.post(`/api/workflows?source=${sourceWorkflowId}`,
			{ name: newName })
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Deletes a given workflow under a given playbook.
	 * @param workflowIdToDelete ID of the workflow to be deleted
	 */
	deleteWorkflow(workflowIdToDelete: string): Promise<void> {
		return this.http.delete(`/api/workflows/${workflowIdToDelete}`)
			.toPromise()
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Creates a new workflow under a given playbook.
	 * @param playbookId ID of the playbook the new workflow should be added under
	 * @param workflow Workflow to be saved
	 */
	newWorkflow(workflow: Workflow): Promise<Workflow> {
		workflow.id = UUID.UUID();
		return this.http.post('/api/workflows', classToPlain(workflow))
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Saves the data of a given workflow specified under a given playbook.
	 * @param workflow Data to be saved under the workflow (actions, etc.)
	 */
	saveWorkflow(workflow: Workflow): Promise<Workflow> {
		return this.http.put(`/api/workflows/${workflow.id}`, classToPlain(workflow))
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Loads the data of a given workflow under a given playbook.
	 * @param workflowId ID of the workflow to load
	 */
	loadWorkflow(workflowId: string): Promise<Workflow> {
		return this.http.get(`/api/workflows/${workflowId}`)
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Notifies the server to execute a given workflow.
	 * Note that execution results are not returned here, but on a separate stream-actions EventSource.
	 * @param workflowId ID of the workflow to execute
	 */
	addWorkflowToQueue(workflowId: string, executionId: string = null): Promise<WorkflowStatus> {
		return this.executionService.addWorkflowToQueue(workflowId, executionId);
	}

	/**
	 * Returns an array of all globals within the DB.
	 */
	getGlobals(): Promise<Variable[]> {
		return this.globalsService.getAllGlobals();
	}

	/**
	 * Gets all app apis from the server.
	 */
	getApis(): Promise<AppApi[]> {
		//return this.http.get('/api/apps/apis')
		//	.toPromise()
		const data = [
			{
			  "action_apis": [
				{
				  "default_return": "Success",
				  "description": "Connect to walkoff",
				  "name": "connect",
				  "parameters": [
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"enum": [
						  "Success"
						],
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "failure": true,
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "failure": true,
					  "schema": {
						"enum": [
						  "Could not locate Walkoff instance"
						],
						"type": "string"
					  },
					  "status": "WalkoffNotFound"
					},
					{
					  "failure": true,
					  "schema": {
						"enum": [
						  "Invalid login"
						],
						"type": "string"
					  },
					  "status": "AuthenticationError"
					},
					{
					  "failure": true,
					  "schema": {
						"description": "Unknown HTTP response from server",
						"type": "string"
					  },
					  "status": "UnknownResponse"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.connect"
				},
				{
				  "default_return": "Success",
				  "description": "Disconnect from walkoff",
				  "name": "disconnect",
				  "parameters": [
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"enum": [
						  "Success"
						],
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "schema": {
						"enum": [
						  "Not connected to Walkoff"
						],
						"type": "string"
					  },
					  "status": "NotConnected"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.disconnect"
				},
				{
				  "default_return": "Success",
				  "description": "Executes a workflow",
				  "name": "execute workflow",
				  "parameters": [
					{
					  "description": "ID of the workflow",
					  "name": "workflow_id",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"items": {
						  "description": "execution_id of the executed workflow in array",
						  "type": "string"
						},
						"type": "array"
					  },
					  "status": "Success"
					},
					{
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "schema": {
						"enum": [
						  "Unauthorized credentials"
						],
						"type": "string"
					  },
					  "status": "Unauthorized"
					},
					{
					  "schema": {
						"enum": [
						  "Not connected to Walkoff"
						],
						"type": "string"
					  },
					  "status": "NotConnected"
					},
					{
					  "schema": {
						"description": "Unknown HTTP response from server",
						"type": "string"
					  },
					  "status": "UnknownResponse"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.execute_workflow"
				},
				{
				  "default_return": "Success",
				  "description": "Gets a list of all the users loaded on the system",
				  "name": "get all users",
				  "parameters": [
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"items": {
						  "properties": {
							"name": {
							  "description": "name of the playbook",
							  "type": "string"
							},
							"workflows": {
							  "description": "the workflows associated with this playbook",
							  "items": {
								"properties": {
								  "name": {
									"description": "name of the workflow",
									"type": "string"
								  },
								  "uid": {
									"description": "UID of the workflow",
									"type": "string"
								  }
								},
								"type": "object"
							  },
							  "type": "array"
							}
						  }
						},
						"type": "array"
					  },
					  "status": "Success"
					},
					{
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "schema": {
						"enum": [
						  "Unauthorized credentials"
						],
						"type": "string"
					  },
					  "status": "Unauthorized"
					},
					{
					  "schema": {
						"enum": [
						  "Not connected to Walkoff"
						],
						"type": "string"
					  },
					  "status": "NotConnected"
					},
					{
					  "schema": {
						"description": "Unknown HTTP response from server",
						"type": "string"
					  },
					  "status": "UnknownResponse"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.get_all_users"
				},
				{
				  "default_return": "Success",
				  "description": "Gets the names and uids of all the workflows loaded on the system",
				  "name": "get all workflows",
				  "parameters": [
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "name": {
							"description": "name of the playbook",
							"type": "string"
						  },
						  "workflows": {
							"description": "the workflows associated with this playbook",
							"items": {
							  "properties": {
								"name": {
								  "description": "name of the workflow",
								  "type": "string"
								},
								"uid": {
								  "description": "UID of the workflow",
								  "type": "string"
								}
							  },
							  "type": "object"
							},
							"type": "array"
						  }
						},
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "schema": {
						"enum": [
						  "Unauthorized credentials"
						],
						"type": "string"
					  },
					  "status": "Unauthorized"
					},
					{
					  "schema": {
						"enum": [
						  "Not connected to Walkoff"
						],
						"type": "string"
					  },
					  "status": "NotConnected"
					},
					{
					  "schema": {
						"description": "Unknown HTTP response from server",
						"type": "string"
					  },
					  "status": "UnknownResponse"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.get_all_workflows"
				},
				{
				  "default_return": "Success",
				  "description": "Get metrics on app usage on this instance",
				  "name": "get app metrics",
				  "parameters": [
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"description": "List of apps with their metrics",
						"properties": {
						  "apps": {
							"items": {
							  "properties": {
								"actions": {
								  "description": "list of actions in an app",
								  "items": {
									"properties": {
									  "error_metrics": {
										"properties": {
										  "avg_time": {
											"description": "average runtime of the action until error",
											"type": "string"
										  },
										  "count": {
											"description": "number of times the action encountered and error",
											"type": "integer"
										  }
										},
										"type": "object"
									  },
									  "name": {
										"description": "Name of action",
										"type": "string"
									  },
									  "success_metrics": {
										"properties": {
										  "avg_time": {
											"description": "average runtime of the action until success",
											"type": "string"
										  },
										  "count": {
											"description": "number of times the action was successfully run",
											"type": "integer"
										  }
										},
										"type": "object"
									  }
									},
									"type": "object"
								  },
								  "type": "array"
								},
								"count": {
								  "description": "Number of times an app has been used",
								  "type": "integer"
								},
								"name": {
								  "description": "App name",
								  "type": "string"
								}
							  },
							  "type": "object"
							},
							"type": "array"
						  }
						},
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "schema": {
						"enum": [
						  "Unauthorized credentials"
						],
						"type": "string"
					  },
					  "status": "Unauthorized"
					},
					{
					  "schema": {
						"enum": [
						  "Not connected to Walkoff"
						],
						"type": "string"
					  },
					  "status": "NotConnected"
					},
					{
					  "schema": {
						"description": "Unknown HTTP response from server",
						"type": "string"
					  },
					  "status": "UnknownResponse"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.get_app_metrics"
				},
				{
				  "default_return": "Success",
				  "description": "Gets the ID of a workflow",
				  "name": "get workflow id",
				  "parameters": [
					{
					  "description": "name of the playbook",
					  "name": "playbook_name",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "name of the workflow",
					  "name": "workflow_name",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "schema": {
						"enum": [
						  "Playbook not found, Workflow not found"
						],
						"type": "string"
					  },
					  "status": "WorkflowNotFound"
					},
					{
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "schema": {
						"enum": [
						  "Unauthorized credentials"
						],
						"type": "string"
					  },
					  "status": "Unauthorized"
					},
					{
					  "schema": {
						"enum": [
						  "Not connected to Walkoff"
						],
						"type": "string"
					  },
					  "status": "NotConnected"
					},
					{
					  "schema": {
						"description": "Unknown HTTP response from server",
						"type": "string"
					  },
					  "status": "UnknownResponse"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.get_workflow_id"
				},
				{
				  "default_return": "Success",
				  "description": "Gets metrics on workflow usage on this instance",
				  "name": "get workflow metrics",
				  "parameters": [
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"description": "list of workflows and their metrics",
						"properties": {
						  "workflows": {
							"items": {
							  "properties": {
								"avg_time": {
								  "description": "average runtime of the workflow",
								  "type": "string"
								},
								"count": {
								  "description": "number of times the workflow has run",
								  "type": "integer"
								},
								"name": {
								  "description": "name of the workflow",
								  "type": "string"
								}
							  },
							  "type": "object"
							},
							"type": "array"
						  }
						},
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "schema": {
						"enum": [
						  "Unauthorized credentials"
						],
						"type": "string"
					  },
					  "status": "Unauthorized"
					},
					{
					  "schema": {
						"enum": [
						  "Not connected to Walkoff"
						],
						"type": "string"
					  },
					  "status": "NotConnected"
					},
					{
					  "schema": {
						"description": "Unknown HTTP response from server",
						"type": "string"
					  },
					  "status": "UnknownResponse"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.get_workflow_metrics"
				},
				{
				  "default_return": "Success",
				  "description": "gets the results of all workflows",
				  "name": "get workflow results",
				  "parameters": [
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "id": {
							"description": "execution uid of the workflow",
							"properties": {
							  "completed_at": {
								"description": "The timestamp of when the workflow completed",
								"example": "2017-05-24 00:43:26.930892",
								"type": "string"
							  },
							  "name": {
								"description": "The name of the workflow. Contains both playbook and workflow information",
								"example": "PlaybookName-WorkflowName",
								"type": "string"
							  },
							  "results": {
								"description": "The results of the workflow actions",
								"items": {
								  "description": "A result of a action execution",
								  "properties": {
									"input": {
									  "description": "The input to the action. Of form {input_name -> value}",
									  "type": "object"
									},
									"name": {
									  "description": "The name of the action",
									  "example": "This One action",
									  "type": "string"
									},
									"result": {
									  "description": "The result of the action",
									  "type": "object"
									},
									"timestamp": {
									  "description": "The timestamp of when the action completed",
									  "example": "2017-05-24 00:43:26.930892",
									  "type": "string"
									},
									"type": {
									  "description": "Success or failure of the action",
									  "enum": [
										"SUCCESS",
										"ERROR"
									  ],
									  "example": "SUCCESS",
									  "type": "string"
									}
								  },
								  "required": [
									"name",
									"result",
									"input",
									"type",
									"timestamp"
								  ],
								  "type": "object"
								},
								"type": "array"
							  },
							  "started_at": {
								"description": "The timestamp of when the workflow completed",
								"example": "2017-05-24 00:42:22.934058",
								"type": "string"
							  },
							  "status": {
								"description": "The status of the workflow",
								"enum": [
								  "completed",
								  "running"
								],
								"type": "string"
							  },
							  "uid": {
								"description": "The UID of the workflow",
								"type": "string"
							  }
							},
							"required": [
							  "name",
							  "started_at",
							  "status",
							  "results",
							  "uid"
							],
							"type": "object"
						  }
						},
						"required": [
						  "id"
						],
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "schema": {
						"enum": [
						  "Unauthorized credentials"
						],
						"type": "string"
					  },
					  "status": "Unauthorized"
					},
					{
					  "schema": {
						"enum": [
						  "Not connected to Walkoff"
						],
						"type": "string"
					  },
					  "status": "NotConnected"
					},
					{
					  "schema": {
						"description": "Unknown HTTP response from server",
						"type": "string"
					  },
					  "status": "UnknownResponse"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.get_workflow_results"
				},
				{
				  "description": "Is Walkoff connected?",
				  "name": "is connected",
				  "parameters": [],
				  "returns": [
					{
					  "schema": {
						"type": "boolean"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.is_connected"
				},
				{
				  "default_return": "Success",
				  "description": "Pauses a workflow with the specified workflow execution ID",
				  "name": "pause workflow",
				  "parameters": [
					{
					  "description": "specific execution_id of the workflow",
					  "name": "execution_id",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "schema": {
						"enum": [
						  "Unauthorized credentials"
						],
						"type": "string"
					  },
					  "status": "Unauthorized"
					},
					{
					  "schema": {
						"enum": [
						  "Not connected to Walkoff"
						],
						"type": "string"
					  },
					  "status": "NotConnected"
					},
					{
					  "schema": {
						"description": "Unknown HTTP response from server",
						"type": "string"
					  },
					  "status": "UnknownResponse"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.pause_workflow"
				},
				{
				  "default_return": "Success",
				  "description": "Resumes a paused workflow with the specified workflow execution id",
				  "name": "resume workflow",
				  "parameters": [
					{
					  "description": "specific execution_id of the workflow",
					  "name": "execution_id",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "schema": {
						"enum": [
						  "Unauthorized credentials"
						],
						"type": "string"
					  },
					  "status": "Unauthorized"
					},
					{
					  "schema": {
						"enum": [
						  "Not connected to Walkoff"
						],
						"type": "string"
					  },
					  "status": "NotConnected"
					},
					{
					  "schema": {
						"description": "Unknown HTTP response from server",
						"type": "string"
					  },
					  "status": "UnknownResponse"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.resume_workflow"
				},
				{
				  "default_return": "Success",
				  "description": "Trigger a workflow",
				  "name": "trigger",
				  "parameters": [
					{
					  "description": "execution_id of workflows to triggers",
					  "name": "execution_ids",
					  "required": true,
					  "schema": {
						"items": {
						  "type": "string"
						},
						"type": "array"
					  }
					},
					{
					  "description": "data to send to waiting workflows",
					  "name": "data",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "Arguments into the starting action",
					  "name": "arguments",
					  "schema": {
						"additionalProperties": true,
						"type": "object"
					  }
					},
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "errors": {
							"description": "The errors executed. Array of the form [{trigger_name -> error message}]",
							"type": "array"
						  },
						  "executed": {
							"description": "The executed workflows",
							"items": {
							  "properties": {
								"id": {
								  "description": "The Execution UID of the workflow executing",
								  "readOnly": true,
								  "type": "string"
								},
								"name": {
								  "description": "The name of the trigger executing",
								  "type": "string"
								}
							  },
							  "required": [
								"id",
								"name"
							  ],
							  "type": "object"
							},
							"type": "array"
						  }
						},
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "schema": {
						"enum": [
						  "Unauthorized credentials"
						],
						"type": "string"
					  },
					  "status": "Unauthorized"
					},
					{
					  "schema": {
						"enum": [
						  "Not connected to Walkoff"
						],
						"type": "string"
					  },
					  "status": "NotConnected"
					},
					{
					  "schema": {
						"description": "Unknown HTTP response from server",
						"type": "string"
					  },
					  "status": "UnknownResponse"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.trigger"
				},
				{
				  "default_return": "Success",
				  "description": "Waits for an executing workflow to complete and gets the results",
				  "name": "wait for workflow completion",
				  "parameters": [
					{
					  "description": "The execution ID of the workflow to wait upon",
					  "name": "execution_id",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "Timeout on the action (in seconds)",
					  "name": "timeout",
					  "schema": {
						"default": 300,
						"type": "number"
					  }
					},
					{
					  "description": "Timeout on the request (in seconds)",
					  "name": "request_timeout",
					  "schema": {
						"default": 2.0,
						"type": "number"
					  }
					},
					{
					  "description": "time to wait in between subsequent requests (in seconds)",
					  "name": "wait_between_requests",
					  "schema": {
						"default": 0.1,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "completed_at": {
							"description": "The timestamp of when the workflow completed",
							"example": "2017-05-24 00:43:26.930892",
							"type": "string"
						  },
						  "name": {
							"description": "The name of the workflow. Contains both playbook and workflow information",
							"example": "PlaybookName-WorkflowName",
							"type": "string"
						  },
						  "results": {
							"description": "The results of the workflow actions",
							"items": {
							  "description": "A result of a action execution",
							  "properties": {
								"input": {
								  "description": "The input to the action. Of form {input_name -> value}",
								  "type": "object"
								},
								"name": {
								  "description": "The name of the action",
								  "example": "This One action",
								  "type": "string"
								},
								"result": {
								  "description": "The result of the action",
								  "type": "object"
								},
								"timestamp": {
								  "description": "The timestamp of when the action completed",
								  "example": "2017-05-24 00:43:26.930892",
								  "type": "string"
								},
								"type": {
								  "description": "Success or failure of the action",
								  "enum": [
									"SUCCESS",
									"ERROR"
								  ],
								  "example": "SUCCESS",
								  "type": "string"
								}
							  },
							  "required": [
								"name",
								"result",
								"input",
								"type",
								"timestamp"
							  ],
							  "type": "object"
							},
							"type": "array"
						  },
						  "started_at": {
							"description": "The timestamp of when the workflow completed",
							"example": "2017-05-24 00:42:22.934058",
							"type": "string"
						  },
						  "status": {
							"description": "The status of the workflow",
							"enum": [
							  "completed",
							  "running"
							],
							"type": "string"
						  },
						  "uid": {
							"description": "The UID of the workflow",
							"type": "string"
						  }
						},
						"required": [
						  "name",
						  "started_at",
						  "status",
						  "results",
						  "uid"
						],
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "schema": {
						"enum": [
						  "Connection timed out"
						],
						"type": "string"
					  },
					  "status": "TimedOut"
					},
					{
					  "schema": {
						"enum": [
						  "Unauthorized credentials"
						],
						"type": "string"
					  },
					  "status": "Unauthorized"
					},
					{
					  "schema": {
						"enum": [
						  "Not connected to Walkoff"
						],
						"type": "string"
					  },
					  "status": "NotConnected"
					},
					{
					  "schema": {
						"description": "Unknown HTTP response from server",
						"type": "string"
					  },
					  "status": "UnknownResponse"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.Walkoff.wait_for_workflow_completion"
				}
			  ],
			  "condition_apis": [],
			  "device_apis": [
				{
				  "description": "Walkoff instance",
				  "fields": [
					{
					  "description": "Username for Walkoff instance",
					  "name": "username",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "Password for Walkoff instance",
					  "encrypted": true,
					  "name": "password",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "IP address of Walkoff instance",
					  "name": "ip",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "Port of Walkoff instance",
					  "name": "port",
					  "required": true,
					  "schema": {
						"maximum": 65355,
						"minimum": 1,
						"type": "integer"
					  }
					},
					{
					  "description": "Whether or not to use HTTPS",
					  "name": "https",
					  "schema": {
						"type": "boolean"
					  }
					}
				  ],
				  "name": "Walkoff"
				}
			  ],
			  "external_docs": [],
			  "info": {
				"contact": {
				  "name": "Walkoff Team"
				},
				"description": "An app to communicate with another Walkoff instance",
				"license": {
				  "name": "Creative Commons"
				},
				"title": "Walkoff App",
				"version": "1.0.0"
			  },
			  "name": "Walkoff",
			  "tags": [],
			  "transform_apis": []
			},
			{
			  "action_apis": [
				{
				  "description": "Basic function which uses the connected device",
				  "name": "action using device",
				  "parameters": [],
				  "returns": [
					{
					  "schema": {
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.SkeletonApp.test_function_with_device_reference"
				},
				{
				  "description": "Basic function which takes in parameter and returns it",
				  "name": "action with params",
				  "parameters": [
					{
					  "description": "The test parameter",
					  "name": "test_param",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "description": "repeated method",
					  "schema": {
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.SkeletonApp.test_function_with_param"
				},
				{
				  "description": "Basic function which does not take in paramaters",
				  "name": "basic",
				  "parameters": [],
				  "returns": [
					{
					  "schema": {
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.SkeletonApp.test_function"
				},
				{
				  "description": "Basic global function",
				  "global": true,
				  "name": "global action",
				  "parameters": [
					{
					  "name": "data",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.test_global_action"
				}
			  ],
			  "condition_apis": [],
			  "device_apis": [
				{
				  "description": "a skeleton device type",
				  "fields": [
					{
					  "name": "username",
					  "placeholder": "enter a username",
					  "required": true,
					  "schema": {
						"maxLength": 20,
						"minLength": 5,
						"type": "string"
					  }
					},
					{
					  "encrypted": true,
					  "name": "password",
					  "placeholder": "enter a password",
					  "schema": {
						"minLength": 5,
						"type": "string"
					  }
					}
				  ],
				  "name": "SkeletonDeviceType"
				}
			  ],
			  "external_docs": [],
			  "info": {
				"contact": {
				  "name": "Walkoff Team"
				},
				"description": "An app template.",
				"license": {
				  "name": "Creative Commons"
				},
				"title": "Skeleton App",
				"version": "1.0.0"
			  },
			  "name": "SkeletonApp",
			  "tags": [],
			  "transform_apis": []
			},
			{
			  "action_apis": [
				{
				  "description": "Returns an introductory message",
				  "global": true,
				  "name": "hello world",
				  "parameters": [],
				  "returns": [
					{
					  "description": "introductory message",
					  "schema": {
						"properties": {
						  "message": {
							"type": "string"
						  }
						},
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.hello_world"
				},
				{
				  "description": "Returns an introductory message",
				  "name": "hello world bound",
				  "parameters": [],
				  "returns": [
					{
					  "description": "introductory message",
					  "schema": {
						"properties": {
						  "message": {
							"type": "string"
						  }
						},
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.HelloWorld.hello_world_bound"
				},
				{
				  "description": "pauses execution for an amount of time",
				  "global": true,
				  "name": "pause",
				  "parameters": [
					{
					  "description": "The seconds to pause for",
					  "name": "seconds",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "description": "successfully paused",
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.pause"
				},
				{
				  "description": "pauses execution for an amount of time",
				  "name": "pause bound",
				  "parameters": [
					{
					  "description": "The seconds to pause for",
					  "name": "seconds",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "description": "successfully paused",
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.HelloWorld.pause_bound"
				},
				{
				  "description": "Repeats the call argument",
				  "global": true,
				  "name": "repeat back to me",
				  "parameters": [
					{
					  "description": "message to repeat",
					  "name": "call",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "description": "repeated method",
					  "schema": {
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.repeat_back_to_me"
				},
				{
				  "description": "Repeats the call argument",
				  "name": "repeat back to me bound",
				  "parameters": [
					{
					  "description": "message to repeat",
					  "name": "call",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "description": "repeated method",
					  "schema": {
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.HelloWorld.repeat_back_to_me_bound"
				},
				{
				  "description": "Increments a given number by 1",
				  "global": true,
				  "name": "return plus one",
				  "parameters": [
					{
					  "description": "number to increment",
					  "name": "number",
					  "required": true,
					  "schema": {
						"format": "int32",
						"type": "integer"
					  }
					}
				  ],
				  "returns": [
					{
					  "description": "incremented number",
					  "schema": {
						"type": "integer"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.return_plus_one"
				},
				{
				  "description": "Increments a given number by 1",
				  "name": "return plus one bound",
				  "parameters": [
					{
					  "description": "number to increment",
					  "name": "number",
					  "required": true,
					  "schema": {
						"format": "int32",
						"type": "integer"
					  }
					}
				  ],
				  "returns": [
					{
					  "description": "incremented number",
					  "schema": {
						"type": "integer"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.HelloWorld.return_plus_one_bound"
				},
				{
				  "description": "gets teh total number of actions which have been called for this app instance",
				  "name": "total actions called",
				  "parameters": [],
				  "returns": [
					{
					  "schema": {
						"minimum": 0,
						"type": "integer"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "app.HelloWorld.total_actions_called"
				}
			  ],
			  "condition_apis": [],
			  "device_apis": [
				{
				  "description": "a test type",
				  "fields": [
					{
					  "name": "Text field",
					  "placeholder": "enter something please",
					  "required": true,
					  "schema": {
						"maxLength": 20,
						"minLength": 5,
						"type": "string"
					  }
					},
					{
					  "encrypted": true,
					  "name": "Encrypted field",
					  "placeholder": "shh its a secret",
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "name": "Number field",
					  "placeholder": "this ones a number",
					  "required": true,
					  "schema": {
						"exclusiveMaximum": true,
						"maximum": 25,
						"minimum": 0,
						"multipleOf": 5,
						"type": "integer"
					  }
					},
					{
					  "name": "Enum field",
					  "placeholder": "this ones a dropdown",
					  "required": true,
					  "schema": {
						"enum": [
						  "val 1",
						  "val 2",
						  "val 3",
						  "another val"
						],
						"type": "string"
					  }
					},
					{
					  "name": "Boolean field",
					  "schema": {
						"type": "boolean"
					  }
					}
				  ],
				  "name": "Test Device Type"
				},
				{
				  "description": "a 2nd test type",
				  "fields": [
					{
					  "name": "Text field",
					  "schema": {
						"maxLength": 100,
						"minLength": 5,
						"pattern": "^([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])$",
						"type": "string"
					  }
					},
					{
					  "name": "Enum field",
					  "schema": {
						"enum": [
						  "val 1",
						  "val 2",
						  "val 3",
						  "another val"
						],
						"type": "string"
					  }
					},
					{
					  "encrypted": true,
					  "name": "Encrypted field",
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "name": "Number field",
					  "schema": {
						"default": 10,
						"type": "number"
					  }
					}
				  ],
				  "name": "Test Device Type 2"
				}
			  ],
			  "external_docs": [],
			  "info": {
				"contact": {
				  "name": "Walkoff Team"
				},
				"description": "A sample walkoff app specification",
				"license": {
				  "name": "Creative Commons"
				},
				"title": "HelloWorldApp",
				"version": "1.0.0"
			  },
			  "name": "HelloWorld",
			  "tags": [],
			  "transform_apis": []
			},
			{
			  "action_apis": [
				{
				  "description": "Gets a list of device IDs that have the specified fields",
				  "global": true,
				  "name": "Get Devices By Fields",
				  "parameters": [
					{
					  "description": "A dictionary of search fields, with the key being the field name and value as field value",
					  "name": "fields",
					  "schema": {
						"type": "object"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"items": {
						  "type": "integer"
						},
						"type": "array"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.get_devices_by_fields"
				},
				{
				  "description": "Rounds a number to the specified number of decimals",
				  "global": true,
				  "name": "Round to N",
				  "parameters": [
					{
					  "description": "Number to round",
					  "name": "number",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "description": "Decimal places to round to",
					  "name": "places",
					  "required": true,
					  "schema": {
						"type": "integer"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "number"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.round_to_n"
				},
				{
				  "description": "Returns random float between 0.0 and 1.0 using system entropy",
				  "global": true,
				  "name": "System PRNG",
				  "parameters": [],
				  "returns": [
					{
					  "schema": {
						"type": "number"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.system_rand"
				},
				{
				  "default_return": "Accepted",
				  "description": "responds to an accept/decline message",
				  "global": true,
				  "name": "accept/decline",
				  "parameters": [
					{
					  "name": "action",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "boolean"
					  },
					  "status": "Accepted"
					},
					{
					  "failure": true,
					  "schema": {
						"type": "boolean"
					  },
					  "status": "Declined"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.accept_decline"
				},
				{
				  "description": "Adds two numbers",
				  "global": true,
				  "name": "add",
				  "parameters": [
					{
					  "description": "The first number",
					  "name": "num1",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "description": "The second number",
					  "name": "num2",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "number"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.add"
				},
				{
				  "description": "Appends an accept decline component to a message",
				  "global": true,
				  "name": "append accept decline message component",
				  "parameters": [
					{
					  "description": "Existing message object",
					  "name": "message",
					  "required": true,
					  "schema": {
						"type": "object"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "body": {
							"description": "body of the message",
							"items": {
							  "properties": {
								"data": {
								  "type": "object"
								},
								"requires_action": {
								  "enum": [
									false
								  ],
								  "type": "boolean"
								},
								"type": {
								  "type": "string"
								}
							  },
							  "required": [
								"type",
								"data",
								"requires_action"
							  ],
							  "type": "object"
							},
							"type": "array"
						  },
						  "subject": {
							"type": "string"
						  }
						},
						"required": [
						  "body"
						],
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.append_accept_decline_message_component"
				},
				{
				  "description": "Appends a text component to a message",
				  "global": true,
				  "name": "append text message component",
				  "parameters": [
					{
					  "description": "Existing message object",
					  "name": "message",
					  "required": true,
					  "schema": {
						"type": "object"
					  }
					},
					{
					  "name": "text",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "body": {
							"description": "body of the message",
							"items": {
							  "properties": {
								"data": {
								  "type": "object"
								},
								"requires_action": {
								  "enum": [
									false
								  ],
								  "type": "boolean"
								},
								"type": {
								  "type": "string"
								}
							  },
							  "required": [
								"type",
								"data",
								"requires_action"
							  ],
							  "type": "object"
							},
							"type": "array"
						  },
						  "subject": {
							"type": "string"
						  }
						},
						"required": [
						  "body"
						],
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.append_text_message_component"
				},
				{
				  "description": "Appends a url component to a message",
				  "global": true,
				  "name": "append url message component",
				  "parameters": [
					{
					  "description": "Existing message object",
					  "name": "message",
					  "required": true,
					  "schema": {
						"type": "object"
					  }
					},
					{
					  "name": "url",
					  "required": true,
					  "schema": {
						"format": "uri",
						"type": "string"
					  }
					},
					{
					  "description": "The title to display for this URL link",
					  "name": "title",
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "body": {
							"description": "body of the message",
							"items": {
							  "properties": {
								"data": {
								  "type": "object"
								},
								"requires_action": {
								  "enum": [
									false
								  ],
								  "type": "boolean"
								},
								"type": {
								  "type": "string"
								}
							  },
							  "required": [
								"type",
								"data",
								"requires_action"
							  ],
							  "type": "object"
							},
							"type": "array"
						  },
						  "subject": {
							"type": "string"
						  }
						},
						"required": [
						  "body"
						],
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.append_url_message_component"
				},
				{
				  "description": "Combines two messages",
				  "global": true,
				  "name": "combine message",
				  "parameters": [
					{
					  "description": "Existing message object",
					  "name": "message1",
					  "required": true,
					  "schema": {
						"type": "object"
					  }
					},
					{
					  "description": "Existing message object to add to message1",
					  "name": "message2",
					  "required": true,
					  "schema": {
						"type": "object"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "body": {
							"description": "body of the message",
							"items": {
							  "properties": {
								"data": {
								  "type": "object"
								},
								"requires_action": {
								  "enum": [
									false
								  ],
								  "type": "boolean"
								},
								"type": {
								  "type": "string"
								}
							  },
							  "required": [
								"type",
								"data",
								"requires_action"
							  ],
							  "type": "object"
							},
							"type": "array"
						  },
						  "subject": {
							"type": "string"
						  }
						},
						"required": [
						  "body"
						],
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.combine_messages"
				},
				{
				  "description": "Creates a component for a message with buttons to accept or decline.",
				  "global": true,
				  "name": "create accept decline message component",
				  "parameters": [],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "data": {
							"type": "object"
						  },
						  "requires_action": {
							"enum": [
							  true
							],
							"type": "boolean"
						  },
						  "type": {
							"type": "string"
						  }
						},
						"required": [
						  "type",
						  "data",
						  "requires_action"
						],
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.create_accept_decline_message_component"
				},
				{
				  "description": "Creates a message with no body",
				  "global": true,
				  "name": "create empty message",
				  "parameters": [
					{
					  "name": "subject",
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "body": {
							"description": "body of the message",
							"items": {
							  "properties": {
								"data": {
								  "type": "object"
								},
								"requires_action": {
								  "enum": [
									false
								  ],
								  "type": "boolean"
								},
								"type": {
								  "type": "string"
								}
							  },
							  "required": [
								"type",
								"data",
								"requires_action"
							  ],
							  "type": "object"
							},
							"type": "array"
						  },
						  "subject": {
							"type": "string"
						  }
						},
						"required": [
						  "body"
						],
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.create_empty_message"
				},
				{
				  "description": "Creates a text component for a message",
				  "global": true,
				  "name": "create text message component",
				  "parameters": [
					{
					  "name": "text",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "data": {
							"properties": {
							  "text": {
								"type": "string"
							  }
							},
							"required": [
							  "text"
							],
							"type": "object"
						  },
						  "requires_action": {
							"enum": [
							  false
							],
							"type": "boolean"
						  },
						  "type": {
							"type": "string"
						  }
						},
						"required": [
						  "type",
						  "data",
						  "requires_action"
						],
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.create_text_message_component"
				},
				{
				  "description": "Creates a url component for a message",
				  "global": true,
				  "name": "create url message component",
				  "parameters": [
					{
					  "name": "url",
					  "required": true,
					  "schema": {
						"format": "uri",
						"type": "string"
					  }
					},
					{
					  "description": "The title to display for this URL link",
					  "name": "title",
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "data": {
							"properties": {
							  "title": {
								"type": "string"
							  },
							  "url": {
								"type": "string"
							  }
							},
							"required": [
							  "url"
							],
							"type": "object"
						  },
						  "requires_action": {
							"enum": [
							  false
							],
							"type": "boolean"
						  },
						  "type": {
							"type": "string"
						  }
						},
						"required": [
						  "type",
						  "data",
						  "requires_action"
						],
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.create_url_message_component"
				},
				{
				  "description": "returns a csv string as an array",
				  "global": true,
				  "name": "csv as array",
				  "parameters": [
					{
					  "description": "csv to return",
					  "name": "data",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "description": "echoed list",
					  "schema": {
						"type": "array"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.csv_as_array"
				},
				{
				  "default_return": "Success",
				  "description": "Reads a CSV file and return a list of JSON objects representing the CSV",
				  "global": true,
				  "name": "csv to json",
				  "parameters": [
					{
					  "description": "path to the csv file",
					  "name": "path",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "name": "separator",
					  "schema": {
						"default": ",",
						"type": "string"
					  }
					},
					{
					  "name": "encoding",
					  "schema": {
						"default": "ascii",
						"type": "string"
					  }
					},
					{
					  "description": "headers to use for teh CSV. If none are provided, the first line of the CSV is used",
					  "name": "headers",
					  "schema": {
						"items": {
						  "type": "string"
						},
						"type": "array"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"items": {
						  "type": "object"
						},
						"type": "array"
					  },
					  "status": "Success"
					},
					{
					  "failure": true,
					  "schema": {
						"type": "string"
					  },
					  "status": "File Error"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.csv_to_json"
				},
				{
				  "description": "Divides a number",
				  "global": true,
				  "name": "divide",
				  "parameters": [
					{
					  "description": "The value to divide",
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "description": "The number to divide the input by",
					  "name": "divisor",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "number"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.divide"
				},
				{
				  "description": "returns the same array passed into it",
				  "global": true,
				  "name": "echo array",
				  "parameters": [
					{
					  "description": "array to echo",
					  "name": "data",
					  "required": true,
					  "schema": {
						"type": "array"
					  }
					}
				  ],
				  "returns": [
					{
					  "description": "echoed list",
					  "schema": {
						"type": "array"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.echo_array"
				},
				{
				  "description": "returns the same object passed into it",
				  "global": true,
				  "name": "echo object",
				  "parameters": [
					{
					  "description": "The data to echo",
					  "name": "data",
					  "required": true,
					  "schema": {
						"type": "object"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.echo_object"
				},
				{
				  "description": "Gets a selected sub element of a json",
				  "global": true,
				  "name": "json select",
				  "parameters": [
					{
					  "description": "Action reference to the json object",
					  "name": "json_reference",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "element of the json",
					  "name": "element",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.json_select"
				},
				{
				  "description": "Linearly scales a value which is limited to some min and max value to a number between a low and high value",
				  "global": true,
				  "name": "linearly scale",
				  "parameters": [
					{
					  "description": "The value to scale",
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "description": "The minimum value of the input (if value less than this, this value acts as a cutoff)",
					  "name": "min_value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "description": "The maximum value of the input (if value less than this, this value acts as a cutoff)",
					  "name": "max_value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "description": "The lowest possible output value",
					  "name": "low_scale",
					  "required": true,
					  "schema": {
						"default": 0.0,
						"type": "number"
					  }
					},
					{
					  "description": "The highest possible output value",
					  "name": "high_scale",
					  "required": true,
					  "schema": {
						"default": 1.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "number"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.linear_scale"
				},
				{
				  "description": "Gets an element from a list",
				  "global": true,
				  "name": "list select",
				  "parameters": [
					{
					  "description": "Action reference to the list from which to select the element",
					  "name": "list_reference",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "The index of the element",
					  "name": "index",
					  "required": true,
					  "schema": {
						"type": "integer"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.list_select"
				},
				{
				  "default_return": "Success",
				  "description": "Mark data as being blacklisted by appending a \"blacklisted\" field to each element of an array of JSON data",
				  "global": true,
				  "name": "mark blacklist",
				  "parameters": [
					{
					  "description": "The data to mark as blacklisted",
					  "name": "data",
					  "required": true,
					  "schema": {
						"type": "array"
					  }
					},
					{
					  "name": "blacklisted",
					  "required": true,
					  "schema": {
						"default": true,
						"type": "boolean"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"items": {
						  "type": "object"
						},
						"type": "array"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.mark_blacklist"
				},
				{
				  "default_return": "Success",
				  "description": "Mark data as being whitelisted by appending a \"whitelisted\" field to each element in an array of JSON data",
				  "global": true,
				  "name": "mark whitelist",
				  "parameters": [
					{
					  "description": "The data to mark as whitelisted",
					  "name": "data",
					  "required": true,
					  "schema": {
						"type": "array"
					  }
					},
					{
					  "name": "whitelisted",
					  "required": true,
					  "schema": {
						"default": true,
						"type": "boolean"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"items": {
						  "type": "object"
						},
						"type": "array"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.mark_whitelist"
				},
				{
				  "default_return": "Success",
				  "description": "Mark data as being whitelisted or blacklisted by appending a \"whitelisted\"  and a \"blacklisted\" field to each element of JSON the data",
				  "global": true,
				  "name": "mark whitelist and blacklist",
				  "parameters": [
					{
					  "description": "The data to mark as whitelisted",
					  "name": "data",
					  "required": true,
					  "schema": {
						"type": "array"
					  }
					},
					{
					  "name": "whitelisted",
					  "required": true,
					  "schema": {
						"default": false,
						"type": "boolean"
					  }
					},
					{
					  "name": "blacklisted",
					  "required": true,
					  "schema": {
						"default": false,
						"type": "boolean"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"items": {
						  "type": "object"
						},
						"type": "array"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.mark_whitelist_blacklist"
				},
				{
				  "description": "Multiplies a number",
				  "global": true,
				  "name": "multiply",
				  "parameters": [
					{
					  "description": "The value to multiply",
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "description": "The number to multiply the input by",
					  "name": "multiplier",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "number"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.multiply"
				},
				{
				  "description": "Pauses execution of a workflow for a given amount of time",
				  "global": true,
				  "name": "pause",
				  "parameters": [
					{
					  "description": "The seconds to pause the execution for",
					  "name": "seconds",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.pause"
				},
				{
				  "global": true,
				  "name": "request user approval",
				  "parameters": [
					{
					  "name": "users",
					  "schema": {
						"items": {
						  "type": "user"
						},
						"type": "array"
					  }
					},
					{
					  "name": "roles",
					  "schema": {
						"items": {
						  "type": "role"
						},
						"type": "array"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"enum": [
						  "success"
						],
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.basic_request_user_approval"
				},
				{
				  "description": "Sends a message",
				  "global": true,
				  "name": "send message",
				  "parameters": [
					{
					  "description": "Existing message object",
					  "name": "message",
					  "required": true,
					  "schema": {
						"type": "object"
					  }
					},
					{
					  "name": "users",
					  "schema": {
						"items": {
						  "type": "user"
						},
						"type": "array"
					  }
					},
					{
					  "name": "roles",
					  "schema": {
						"items": {
						  "type": "role"
						},
						"type": "array"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"enum": [
						  "success"
						],
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.send_full_message"
				},
				{
				  "description": "Send a text only message to users",
				  "global": true,
				  "name": "send text message",
				  "parameters": [
					{
					  "name": "subject",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "name": "message",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "name": "users",
					  "schema": {
						"items": {
						  "type": "user"
						},
						"type": "array"
					  }
					},
					{
					  "name": "roles",
					  "schema": {
						"items": {
						  "type": "role"
						},
						"type": "array"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"enum": [
						  "success"
						],
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.send_text_message"
				},
				{
				  "description": "Sets the subject of a message",
				  "global": true,
				  "name": "set message subject",
				  "parameters": [
					{
					  "description": "Existing message object",
					  "name": "message",
					  "required": true,
					  "schema": {
						"type": "object"
					  }
					},
					{
					  "name": "subject",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"properties": {
						  "body": {
							"description": "body of the message",
							"items": {
							  "properties": {
								"data": {
								  "type": "object"
								},
								"requires_action": {
								  "enum": [
									false
								  ],
								  "type": "boolean"
								},
								"type": {
								  "type": "string"
								}
							  },
							  "required": [
								"type",
								"data",
								"requires_action"
							  ],
							  "type": "object"
							},
							"type": "array"
						  },
						  "subject": {
							"type": "string"
						  }
						},
						"required": [
						  "body"
						],
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.set_message_subject"
				},
				{
				  "description": "Subtracts a number from another number",
				  "global": true,
				  "name": "subtract",
				  "parameters": [
					{
					  "description": "The starting value",
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "description": "The number to subtract from the input value",
					  "name": "subtractor",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "number"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.subtract"
				},
				{
				  "description": "Writes a list of IPs to a CSV file",
				  "global": true,
				  "name": "write IPs to CSV",
				  "parameters": [
					{
					  "description": "Action reference to the list of IPs",
					  "name": "ips_reference",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "The path to the CSV file to be written to",
					  "name": "path",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "string"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "actions.write_ips_to_csv"
				}
			  ],
			  "condition_apis": [
				{
				  "data_in": "value",
				  "description": "Used for accept/decline action from messages. If used as a trigger, next action will only run if authorized user clicks \"accept\"",
				  "global": true,
				  "name": "accept/decline",
				  "parameters": [
					{
					  "description": "accept or decline",
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "run": "conditions.accept_decline"
				},
				{
				  "data_in": "value",
				  "global": true,
				  "name": "always false",
				  "parameters": [
					{
					  "description": "the input value",
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "run": "conditions.always_false"
				},
				{
				  "data_in": "value",
				  "global": true,
				  "name": "always true",
				  "parameters": [
					{
					  "description": "the input value",
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "run": "conditions.always_true"
				},
				{
				  "data_in": "value",
				  "global": true,
				  "name": "echo boolean",
				  "parameters": [
					{
					  "description": "the input value",
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "boolean"
					  }
					}
				  ],
				  "run": "conditions.echo_boolean"
				},
				{
				  "data_in": "value",
				  "description": "Compares two numbers",
				  "global": true,
				  "name": "number compare",
				  "parameters": [
					{
					  "description": "The input value",
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "description": "The comparison operator ('g', 'ge', etc.)",
					  "name": "operator",
					  "required": true,
					  "schema": {
						"default": "e",
						"enum": [
						  "g",
						  "ge",
						  "l",
						  "le",
						  "e"
						],
						"type": "string"
					  }
					},
					{
					  "description": "The value with which to compare the input",
					  "name": "threshold",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "run": "conditions.count"
				},
				{
				  "data_in": "value",
				  "description": "Matches an input against a regular expression",
				  "global": true,
				  "name": "regex match",
				  "parameters": [
					{
					  "description": "The input value",
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					},
					{
					  "description": "The regular expression to match",
					  "name": "regex",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "run": "conditions.regMatch"
				},
				{
				  "data_in": "value",
				  "description": "Returns the inverse of the boolean value provided",
				  "global": true,
				  "name": "reverse boolean",
				  "parameters": [
					{
					  "description": "the input value",
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "boolean"
					  }
					}
				  ],
				  "run": "conditions.reverse_boolean"
				}
			  ],
			  "device_apis": [],
			  "external_docs": [],
			  "info": {
				"contact": {
				  "name": "Walkoff Team"
				},
				"description": "Miscellaneous utility actions",
				"license": {
				  "name": "Creative Commons"
				},
				"title": "Utilities",
				"version": "1.0.0"
			  },
			  "name": "Utilities",
			  "tags": [],
			  "transform_apis": [
				{
				  "data_in": "num1",
				  "description": "Adds a number",
				  "global": true,
				  "name": "add",
				  "parameters": [
					{
					  "name": "num1",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "name": "num2",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "number"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "transforms.add"
				},
				{
				  "data_in": "value",
				  "description": "Divides a number",
				  "global": true,
				  "name": "divide",
				  "parameters": [
					{
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "name": "divisor",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "number"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "transforms.divide"
				},
				{
				  "data_in": "value",
				  "description": "Returns the length of a collection",
				  "global": true,
				  "name": "length",
				  "parameters": [
					{
					  "description": "The input collection",
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "description": "The length of the collection",
					  "schema": {
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "transforms.length"
				},
				{
				  "data_in": "value",
				  "description": "Scale a value linearly between a minimum and a maximum.",
				  "global": true,
				  "name": "linear scale",
				  "parameters": [
					{
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "description": "minimum value of the input",
					  "name": "min_value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "description": "maximum value of the input",
					  "name": "max_value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "description": "minimum value of the output",
					  "name": "low_scale",
					  "required": true,
					  "schema": {
						"default": 0.0,
						"type": "number"
					  }
					},
					{
					  "description": "maximum value of the output",
					  "name": "high_scale",
					  "required": true,
					  "schema": {
						"default": 1.0,
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "number"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "transforms.linear_scale"
				},
				{
				  "data_in": "value",
				  "description": "Multiplies a number",
				  "global": true,
				  "name": "multiply",
				  "parameters": [
					{
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "name": "multiplier",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "number"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "transforms.multiply"
				},
				{
				  "data_in": "json_in",
				  "description": "selects an element from a JSON object",
				  "global": true,
				  "name": "select json",
				  "parameters": [
					{
					  "name": "json_in",
					  "required": true,
					  "schema": {
						"type": "object"
					  }
					},
					{
					  "name": "element",
					  "required": true,
					  "schema": {
						"type": "string"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "transforms.json_select"
				},
				{
				  "data_in": "list_in",
				  "description": "selects an element from a list",
				  "global": true,
				  "name": "select list",
				  "parameters": [
					{
					  "name": "list_in",
					  "required": true,
					  "schema": {
						"type": "object"
					  }
					},
					{
					  "name": "index",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "object"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "transforms.list_select"
				},
				{
				  "data_in": "value",
				  "description": "Subtracts a number from the input",
				  "global": true,
				  "name": "subtract",
				  "parameters": [
					{
					  "name": "value",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					},
					{
					  "name": "subtrahend",
					  "required": true,
					  "schema": {
						"type": "number"
					  }
					}
				  ],
				  "returns": [
					{
					  "schema": {
						"type": "number"
					  },
					  "status": "Success"
					},
					{
					  "description": "Exception occurred in action",
					  "failure": true,
					  "status": "UnhandledException"
					},
					{
					  "description": "Input into the action was invalid",
					  "failure": true,
					  "status": "InvalidInput"
					}
				  ],
				  "run": "transforms.subtract"
				}
			  ]
			}
		  ];
		return Promise.resolve(data)
		    .then((data) => plainToClass(AppApi, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Returns an array of all users within the DB.
	 */
	getUsers(): Promise<User[]> {
		return this.settingsService.getAllUsers();
	}

	/**
	 * Returns an array of all roles within the application.
	 */
	getRoles(): Promise<Role[]> {
		return this.settingsService.getRoles();
	}
}
