import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';
import { plainToClass } from 'class-transformer';

import { ScheduledTask } from '../models/scheduler/scheduledTask';
import { Playbook } from '../models/playbook/playbook';
import { UtilitiesService } from '../utilities.service';
import { Workflow } from '../models/playbook/workflow';

const schedulerStatusNumberMapping: { [key: number]: string } = {
	0: 'stopped',
	1: 'running',
	2: 'paused',
};

@Injectable()
export class SchedulerService {
	constructor (private http: HttpClient, private utils: UtilitiesService) {}

	getSchedulerStatus(): Promise<string> {
		return this.http.get('api/scheduler/')
			.toPromise()
			.then((statusObj: any) => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.utils.handleResponseError);
	}

	changeSchedulerStatus(status: string): Promise<string> {
		return this.http.put('api/scheduler/', { status })
			.toPromise()
			.then((statusObj: any) => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.utils.handleResponseError);
	}

	getAllScheduledTasks(): Promise<ScheduledTask[]> {
		return this.utils.paginateAll<ScheduledTask>(this.getScheduledTasks.bind(this));
	}

	getScheduledTasks(page: number = 1): Promise<ScheduledTask[]> {
		return this.http.get(`api/scheduler/tasks/?page=${ page }`)
			.toPromise()
			.then((data: object[]) => plainToClass(ScheduledTask, data))
			.catch(this.utils.handleResponseError);
	}

	addScheduledTask(scheduledTask: ScheduledTask): Promise<ScheduledTask> {
		return this.http.post('api/scheduler/tasks/', scheduledTask)
			.toPromise()
			.then((data: object) => plainToClass(ScheduledTask, data))
			.catch(this.utils.handleResponseError);
	}

	editScheduledTask(scheduledTask: ScheduledTask): Promise<ScheduledTask> {
		return this.http.put(`api/scheduler/tasks/${ scheduledTask.id }`, scheduledTask)
			.toPromise()
			.then((data: object) => plainToClass(ScheduledTask, data))
			.catch(this.utils.handleResponseError);
	}

	deleteScheduledTask(scheduledTaskId: number): Promise<void> {
		return this.http.delete(`api/scheduler/tasks/${scheduledTaskId}`)
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	changeScheduledTaskStatus(scheduledTaskId: number, actionName: string): Promise<void> {
		return this.http.patch(`api/scheduler/tasks/${ scheduledTaskId }`, { action: actionName })
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	getWorkflows(): Promise<Workflow[]> {
		return this.http.get('api/workflows/')
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}
}
