import { Injectable } 			from '@angular/core';
import { Http, Headers, Response, RequestOptions } 		from '@angular/http';

import { Observable }     from 'rxjs/Observable';
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
	requestOptions : RequestOptions;

	constructor (private http: Http) {
		let authKey = localStorage.getItem('authKey');
		let headers = new Headers({ 'Accept': 'application/json' });
		headers.append('Authentication-Token', authKey);

		this.requestOptions = new RequestOptions({ headers: headers });
	}

	//TODO: route should most likely be GET
	executeWorkflow(playbook: string, workflow: string) : Promise<void> {
		return this.http.post(`/playbooks/${playbook}/workflows/${workflow}/execute`, {}, this.requestOptions)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getSchedulerStatus() : Promise<string> {
		return this.http.get('/api/scheduler', this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(statusObj => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.handleError);
	}

	changeSchedulerStatus(status: string) : Promise<string> {
		return this.http.get(`/api/scheduler/${status}`, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(statusObj => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.handleError);
	}

	getScheduledTasks() : Promise<ScheduledTask[]> {
		return this.http.get('/api/scheduledtask', this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(scheduledTasks => scheduledTasks as ScheduledTask[])
			.catch(this.handleError);
	}

	addScheduledTask(scheduledTask: ScheduledTask) : Promise<ScheduledTask> {
		return this.http.put('/api/scheduledtask', scheduledTask, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(scheduledTask => scheduledTask as ScheduledTask)
			.catch(this.handleError);
	}

	editScheduledTask(scheduledTask: ScheduledTask) : Promise<ScheduledTask> {
		return this.http.post('/api/scheduledtask', scheduledTask, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(scheduledTask => scheduledTask as ScheduledTask)
			.catch(this.handleError);
	}

	deleteScheduledTask(scheduledTaskId: number) : Promise<void> {
		return this.http.delete(`/api/scheduledtask/${scheduledTaskId}`, this.requestOptions)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	enableScheduledTask(scheduledTaskId: number): Promise<void> {
		return this.http.get(`/api/scheduledtask/${scheduledTaskId}/enable`, this.requestOptions)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	disableScheduledTask(scheduledTaskId: number): Promise<void> {
		return this.http.get(`/api/scheduledtask/${scheduledTaskId}/disable`, this.requestOptions)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getPlaybooks() : Promise<any> {
		return this.http.get('/api/playbooks', this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	private extractData (res: Response) {
		let body = res.json();
		return body || {};
	}

	private handleError (error: Response | any) {
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
