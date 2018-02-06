import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';
import 'rxjs/add/operator/toPromise';

import { WorkflowStatus } from '../models/execution/workflowStatus';
import { Playbook } from '../models/playbook/playbook';
import { ActionResult } from '../models/execution/actionResult';

@Injectable()
export class ExecutionService {
	constructor (private authHttp: JwtHttp) {}

	performWorkflowStatusAction(playbookId: string, workflowId: string, action: string): Promise<WorkflowStatus> {
		return this.authHttp.post(`api/playbooks/${playbookId}/workflows/${workflowId}/${action}`, {})
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getWorkflowStatuses(): Promise<WorkflowStatus[]> {
		return this.authHttp.get('api/workflowstatus')
			.toPromise()
			.then(this.extractData)
			.then(workflowStatuses => workflowStatuses as WorkflowStatus[])
			.catch(this.handleError);
	}

	getActionResultsForWorkflow(workflowId: string): Promise<ActionResult[]> {
		return this.authHttp.get(`api/workflowstatus/${workflowId}`)
			.toPromise()
			.then(this.extractData)
			.then(actionResults => actionResults as WorkflowStatus[])
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
