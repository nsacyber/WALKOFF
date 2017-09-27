import { Injectable } from '@angular/core';
import { Http, Response, Headers } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Workflow } from '../models/playbook/workflow';
import { Playbook } from '../models/playbook/playbook';
import { Condition } from '../models/playbook/condition';
import { Transform } from '../models/playbook/transform';
import { Device } from '../models/device';

@Injectable()
export class PlaybookService {
	constructor (private authHttp: JwtHttp) {}

	getPlaybooks() : Promise<Playbook> {
		return this.authHttp.get(`/api/playbooks/`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Playbook)
			.catch(this.handleError);
	}

	renamePlaybook(oldName: string, newName: string) : Promise<void> {
		return this.authHttp.post(`/api/playbooks/${oldName}`, { new_name: newName })
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	duplicatePlaybook(oldName: string, newName: string) : Promise<void> {
		return this.authHttp.post(`/api/playbooks/${oldName}`, { playbook: newName })
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	deletePlaybook(playbookToDelete: string) : Promise<void> {
		return this.authHttp.delete(`/api/playbooks/${playbookToDelete}`)
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	renameWorkflow(playbook: string, oldName: string, newName: string) : Promise<void> {
		return this.authHttp.post(`/api/playbooks/${playbook}/workflows/${oldName}`, { new_name: newName })
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	// TODO: probably don't need playbook in body, verify on server
	duplicateWorkflow(playbook: string, oldName: string, newName: string) : Promise<void> {
		return this.authHttp.post(`/api/playbooks/${playbook}/workflows/${oldName}/copy`, { playbook: playbook, workflow: newName })
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	deleteWorkflow(playbook: string, workflowToDelete: string) : Promise<void> {
		return this.authHttp.delete(`/api/playbooks/${playbook}/workflows/${workflowToDelete}`)
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	newWorkflow(playbook: string, workflow: string) : Promise<void> {
		return this.authHttp.put(`/api/playbooks/${playbook}/workflows`, { name: workflow })
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	saveWorkflow(playbook: string, workflow: string, workflowData: Object) : Promise<void> {
		return this.authHttp.post(`/api/playbooks/${playbook}/workflows/${workflow}/save`, { data: workflowData })
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	loadWorkflow(playbook: string, workflow: string) : Promise<Workflow> {
		return this.authHttp.get(`/api/playbooks/${playbook}/workflows/${workflow}`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Workflow)
			.catch(this.handleError);
	}

	executeWorkflow(playbook: string, workflow: string) : Promise<void> {
		return this.authHttp.post(`/api/playbooks/${playbook}/workflows/${workflow}/execute`, {})
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	// TODO: currently an any type, should probably be some sort of 
	getActionsForApps() : Promise<{ [key: string] : string[] }> {
		return this.authHttp.get(`/api/apps/actions`, {})
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	getDevices() : Promise<Device[]> {
		return this.authHttp.get(`/api/devices`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device[])
			.catch(this.handleError);
	}
	
	getConditions() : Promise<Condition[]> {
		return this.authHttp.get(`/api/conditions`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Condition[])
			.catch(this.handleError);
	}

	getTransforms() : Promise<Transform[]> {
		return this.authHttp.get(`/api/transforms`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Transform[])
			.catch(this.handleError);
	}

	private extractData (res: Response) {
		let body = res.json();
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