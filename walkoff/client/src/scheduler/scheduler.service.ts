import { Injectable } from '@angular/core';
import { JwtHttp } from 'angular2-jwt-refresh';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';
import { plainToClass } from 'class-transformer';

import { ScheduledTask } from '../models/scheduler/scheduledTask';
import { Playbook } from '../models/playbook/playbook';
import { UtilitiesService } from '../utilities.service';

const schedulerStatusNumberMapping: { [key: number]: string } = {
	0: 'stopped',
	1: 'running',
	2: 'paused',
};

@Injectable()
export class SchedulerService {
	constructor (private authHttp: JwtHttp, private utils: UtilitiesService) {}

	getSchedulerStatus(): Promise<string> {
		return this.authHttp.get('/api/scheduler')
			.toPromise()
			.then(this.utils.extractResponseData)
			.then(statusObj => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.utils.handleResponseError);
	}

	changeSchedulerStatus(status: string): Promise<string> {
		return this.authHttp.put('/api/scheduler', { status })
			.toPromise()
			.then(this.utils.extractResponseData)
			.then(statusObj => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.utils.handleResponseError);
	}

	getAllScheduledTasks(): Promise<ScheduledTask[]> {
		return this.utils.paginateAll<ScheduledTask>(this.getScheduledTasks.bind(this));
	}

	getScheduledTasks(page: number = 1): Promise<ScheduledTask[]> {
		return this.authHttp.get(`/api/scheduledtasks?page=${ page }`)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object[]) => plainToClass(ScheduledTask, data))
			.catch(this.utils.handleResponseError);
	}

	addScheduledTask(scheduledTask: ScheduledTask): Promise<ScheduledTask> {
		return this.authHttp.post('/api/scheduledtasks', scheduledTask)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object) => plainToClass(ScheduledTask, data))
			.catch(this.utils.handleResponseError);
	}

	editScheduledTask(scheduledTask: ScheduledTask): Promise<ScheduledTask> {
		return this.authHttp.put('/api/scheduledtasks', scheduledTask)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object) => plainToClass(ScheduledTask, data))
			.catch(this.utils.handleResponseError);
	}

	deleteScheduledTask(scheduledTaskId: number): Promise<void> {
		return this.authHttp.delete(`/api/scheduledtasks/${scheduledTaskId}`)
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	changeScheduledTaskStatus(scheduledTaskId: number, actionName: string): Promise<void> {
		return this.authHttp.patch('/api/scheduledtasks', { id: scheduledTaskId, action: actionName })
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	getPlaybooks(): Promise<Playbook[]> {
		return this.authHttp.get('/api/playbooks')
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object[]) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}
}
