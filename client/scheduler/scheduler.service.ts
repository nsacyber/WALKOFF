import { Injectable } from '@angular/core';
import { Http, Headers, Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';

import { AvailableSubscription } from '../models/availableSubscription';
import { Case } from '../models/case';
import { ScheduledTask } from '../models/scheduledTask';

const schedulerStatusNumberMapping: any = {
	"0": "stopped",
	"1": "running",
	"2": "paused"
};

@Injectable()
export class SchedulerService {
	constructor (private authHttp: JwtHttp) {
	}

	//TODO: route should most likely be GET
	executeWorkflow(playbook: string, workflow: string) : Promise<void> {
		return this.authHttp.post(`/playbooks/${playbook}/workflows/${workflow}/execute`, {})
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getSchedulerStatus() : Promise<string> {
		return this.authHttp.get('/api/scheduler')
			.toPromise()
			.then(this.extractData)
			.then(statusObj => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.handleError);
	}

	changeSchedulerStatus(status: string) : Promise<string> {
		return this.authHttp.get(`/api/scheduler/${status}`)
			.toPromise()
			.then(this.extractData)
			.then(statusObj => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.handleError);
	}

	getScheduledTasks() : Promise<ScheduledTask[]> {
		return this.authHttp.get('/api/scheduledtasks')
			.toPromise()
			.then(this.extractData)
			.then(scheduledTasks => scheduledTasks as ScheduledTask[])
			.catch(this.handleError);
	}

	addScheduledTask(scheduledTask: ScheduledTask) : Promise<ScheduledTask> {
		return this.authHttp.put('/api/scheduledtasks', scheduledTask)
			.toPromise()
			.then(this.extractData)
			.then(scheduledTask => scheduledTask as ScheduledTask)
			.catch(this.handleError);
	}

	editScheduledTask(scheduledTask: ScheduledTask) : Promise<ScheduledTask> {
		return this.authHttp.post('/api/scheduledtasks', scheduledTask)
			.toPromise()
			.then(this.extractData)
			.then(scheduledTask => scheduledTask as ScheduledTask)
			.catch(this.handleError);
	}

	deleteScheduledTask(scheduledTaskId: number) : Promise<void> {
		return this.authHttp.delete(`/api/scheduledtasks/${scheduledTaskId}`)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	changeScheduledTaskStatus(scheduledTaskId: number, action: string): Promise<void> {
		return this.authHttp.put(`/api/scheduledtasks/${scheduledTaskId}/${action}`, {})
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getPlaybooks() : Promise<any> {
		return this.authHttp.get('/api/playbooks')
			.toPromise()
			.then(this.extractData)
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
