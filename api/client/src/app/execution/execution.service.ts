import { Injectable } from '@angular/core';
import 'rxjs/add/operator/toPromise';
import { plainToClass, classToPlain } from 'class-transformer';
import { HttpClient } from '@angular/common/http';

import { WorkflowStatus } from '../models/execution/workflowStatus';
import { Playbook } from '../models/playbook/playbook';
import { Workflow } from '../models/playbook/workflow';
import { EnvironmentVariable } from '../models/playbook/environmentVariable';
import { UtilitiesService } from '../utilities.service';

@Injectable({
	providedIn: 'root'
})
export class ExecutionService {
	constructor (private http: HttpClient, private utils: UtilitiesService) {}

	/**
	 * Asyncronously adds a workflow (by ID) to the queue to be executed.
	 * Returns the new workflow status for the workflow execution.
	 * @param workflowId Workflow Id to queue
	 */
	addWorkflowToQueue(workflow_id: string, execution_id: string = null, variables: EnvironmentVariable[] = []): Promise<WorkflowStatus> {
		let data: any = { workflow_id };
		if (execution_id) data.execution_id = execution_id;
		if (variables.length > 0) data.workflow_variables = classToPlain(variables);

		return this.http.post('api/workflowqueue/', data)
			.toPromise()
			.then((data: object) => plainToClass(WorkflowStatus, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * For a given executing workflow, asyncronously perform some action to change its status.
	 * Only returns success
	 * @param executionId Execution ID to act upon
	 * @param action Action to take (e.g. abort, resume, pause)
	 */
	performWorkflowStatusAction(executionId: string, action: string): Promise<void> {
		return this.http.patch(`api/workflowqueue/${ executionId }`, { status: action })
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	/**
	 * For a given executing workflow, asyncronously perform some action to change its status.
	 * Only returns success
	 * @param executionId Execution ID to act upon
	 * @param action Action to take (e.g. abort, resume, pause)
	 */
	performWorkflowTrigger(executionId: string, trigger: string, data = {}): Promise<void> {
		return this.http.patch(`api/workflowqueue/${ executionId }`, { status: 'trigger',  trigger_id: trigger, trigger_data: data})
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asyncronously gets an array of workflow statuses from the server.
	 */
	getAllWorkflowStatuses(): Promise<WorkflowStatus[]> {
		return this.utils.paginateAll<WorkflowStatus>(this.getWorkflowStatuses.bind(this));
	}

	/**
	 * Asyncronously gets an array of workflow statuses from the server.
	 */
	getWorkflowStatuses(page: number = 1): Promise<WorkflowStatus[]> {
		return this.http.get(`api/workflowqueue/?page=${ page }`)
			.toPromise()
			.then((data: object[]) => plainToClass(WorkflowStatus, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asyncronously gets the full information for a given workflow status, including action statuses.
	 * @param workflowExecutionId Workflow Status to query
	 */
	getWorkflowStatus(workflowExecutionId: string): Promise<WorkflowStatus> {
		return this.http.get(`api/workflowqueue/${workflowExecutionId}`)
			.toPromise()
			.then((data: object) => plainToClass(WorkflowStatus, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asyncryonously gets arrays of all playbooks and workflows (id, name pairs only).
	 */
	getPlaybooks(): Promise<Playbook[]> {
		return this.http.get('api/playbooks')
			.toPromise()
			.then((data: object[]) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Returns all playbooks and their child workflows in minimal form (id, name).
	 */
	getWorkflows(): Promise<Workflow[]> {
		return this.http.get('api/workflows/')
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Loads the data of a given workflow under a given playbook.
	 * @param workflowId ID of the workflow to load
	 */
	loadWorkflow(workflowId: string): Promise<Workflow> {
		return this.http.get(`api/workflows/${workflowId}`)
			.toPromise()
			.then((data: object) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}

	async getLatestExecution(workflowId: string): Promise<WorkflowStatus> {
		const workflowStatuses = await this.getAllWorkflowStatuses();
		const workflowStatus = workflowStatuses.filter(status => status.workflow_id = workflowId && status.completed_at).find(e => !!e);
		return this.getWorkflowStatus(workflowStatus.execution_id);
	}
}
