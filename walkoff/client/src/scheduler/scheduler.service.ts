import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';

import { ScheduledTask } from '../models/scheduledTask';
import { Playbook } from '../models/playbook/playbook';

const schedulerStatusNumberMapping: any = {
	0: 'stopped',
	1: 'running',
	2: 'paused',
};

@Injectable()
export class SchedulerService {
	constructor (private authHttp: JwtHttp) {
	}

	//TODO: route should most likely be GET
	executeWorkflow(playbook: string, workflow: string): Promise<void> {
		return this.authHttp.post(`/playbooks/${playbook}/workflows/${workflow}/execute`, {})
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getSchedulerStatus(): Promise<string> {
		return this.authHttp.get('/api/scheduler')
			.toPromise()
			.then(this.extractData)
			.then(statusObj => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.handleError);
	}

	changeSchedulerStatus(status: string): Promise<string> {
		return this.authHttp.get(`/api/scheduler/${status}`)
			.toPromise()
			.then(this.extractData)
			.then(statusObj => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.handleError);
	}

	getScheduledTasks(): Promise<ScheduledTask[]> {
		return this.authHttp.get('/api/scheduledtasks')
			.toPromise()
			.then(this.extractData)
			.then(scheduledTasks => scheduledTasks as ScheduledTask[])
			.catch(this.handleError);
	}

	addScheduledTask(scheduledTask: ScheduledTask): Promise<ScheduledTask> {
		return this.authHttp.put('/api/scheduledtasks', scheduledTask)
			.toPromise()
			.then(this.extractData)
			.then(newScheduledTask => newScheduledTask as ScheduledTask)
			.catch(this.handleError);
	}

	editScheduledTask(scheduledTask: ScheduledTask): Promise<ScheduledTask> {
		return this.authHttp.post('/api/scheduledtasks', scheduledTask)
			.toPromise()
			.then(this.extractData)
			.then(editedScheduledTask => editedScheduledTask as ScheduledTask)
			.catch(this.handleError);
	}

	deleteScheduledTask(scheduledTaskId: number): Promise<void> {
		return this.authHttp.delete(`/api/scheduledtasks/${scheduledTaskId}`)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	changeScheduledTaskStatus(scheduledTaskId: number, actionName: string): Promise<void> {
		return this.authHttp.put(`/api/scheduledtasks/${scheduledTaskId}/${actionName}`, {})
			.toPromise()
			.then(() => null)
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
