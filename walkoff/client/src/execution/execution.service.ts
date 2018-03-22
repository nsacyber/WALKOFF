import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';
import 'rxjs/add/operator/toPromise';
import { plainToClass } from 'class-transformer';

import { WorkflowStatus } from '../models/execution/workflowStatus';
import { Playbook } from '../models/playbook/playbook';

@Injectable()
export class ExecutionService {
	constructor (private authHttp: JwtHttp) {}

	/**
	 * Asyncronously adds a workflow (by ID) to the queue to be executed.
	 * Returns the new workflow status for the workflow execution.
	 * @param workflowId Workflow Id to queue
	 */
	addWorkflowToQueue(workflowId: string): Promise<WorkflowStatus> {
		return this.authHttp.post('api/workflowqueue', { workflow_id: workflowId })
			.toPromise()
			.then(this.extractData)
			.then((data: object) => plainToClass(WorkflowStatus, data))
			.catch(this.handleError);
	}

	/**
	 * For a given executing workflow, asyncronously perform some action to change its status.
	 * Only returns success
	 * @param workflowId Workflow ID to act upon
	 * @param action Action to take (e.g. abort, resume, pause)
	 */
	performWorkflowStatusAction(workflowId: string, action: string): Promise<void> {
		return this.authHttp.patch('api/workflowqueue', { execution_id: workflowId, status: action })
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	/**
	 * Asyncronously gets an array of workflow statuses from the server.
	 */
	getWorkflowStatusList(): Promise<WorkflowStatus[]> {
		return this.authHttp.get('api/workflowqueue')
			.toPromise()
			.then(this.extractData)
			.then((data: object[]) => plainToClass(WorkflowStatus, data))
			.catch(this.handleError);
	}

	/**
	 * Asyncronously gets the full information for a given workflow status, including action statuses.
	 * @param workflowExecutionId Workflow Status to query
	 */
	getWorkflowStatus(workflowExecutionId: string): Promise<WorkflowStatus> {
		return this.authHttp.get(`api/workflowqueue/${workflowExecutionId}`)
			.toPromise()
			.then(this.extractData)
			.then((data: object) => plainToClass(WorkflowStatus, data))
			.catch(this.handleError);
	}

	/**
	 * Asyncryonously gets arrays of all playbooks and workflows (id, name pairs only).
	 */
	getPlaybooks(): Promise<Playbook[]> {
		return this.authHttp.get('/api/playbooks')
			.toPromise()
			.then(this.extractData)
			.then((data: object[]) => plainToClass(Playbook, data))
			.catch(this.handleError);
	}

	private extractData (res: Response) {
		const body = res.json();
		return body || {};
	}

	private handleError (error: Response | any): Promise<any> {
		let errMsg: string;
		let err: string;
		if (error instanceof Response) {
			const body = error.json() || '';
			err = body.error || body.detail || JSON.stringify(body);
			errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
		} else {
			err = errMsg = error.message ? error.message : error.toString();
		}
		console.error(errMsg);
		throw new Error(err);
	}
}
