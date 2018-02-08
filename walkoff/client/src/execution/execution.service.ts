import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';
import 'rxjs/add/operator/toPromise';

import { WorkflowStatus } from '../models/execution/workflowStatus';
import { Playbook } from '../models/playbook/playbook';

@Injectable()
export class ExecutionService {
	constructor (private authHttp: JwtHttp) {}

	addWorkflowToQueue(workflowId: string): Promise<WorkflowStatus> {
		return this.authHttp.post('api/workflowqueue', { workflow_id: workflowId })
			.toPromise()
			.then(this.extractData)
			.then(workflowStatuses => workflowStatuses as WorkflowStatus)
			.catch(this.handleError);
	}

	performWorkflowStatusAction(workflowId: string, action: string): Promise<WorkflowStatus> {
		return this.authHttp.patch('api/workflowqueue', { workflow_execution_id: workflowId, status: action })
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getWorkflowStatusList(): Promise<WorkflowStatus[]> {
		return this.authHttp.get('api/workflowqueue')
			.toPromise()
			.then(this.extractData)
			.then(workflowStatuses => workflowStatuses as WorkflowStatus[])
			.catch(this.handleError);
	}

	getWorkflowStatus(workflowExecutionId: string): Promise<WorkflowStatus> {
		return this.authHttp.get(`api/workflowqueue/${workflowExecutionId}`)
			.toPromise()
			.then(this.extractData)
			.then(workflowStatus => workflowStatus as WorkflowStatus)
			.catch(this.handleError);
	}

	getPlaybooks(): Promise<Playbook[]> {
		return this.authHttp.get('/api/playbooks')
			.toPromise()
			.then(this.extractData)
			.then(playbooks => playbooks as Playbook[])
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
