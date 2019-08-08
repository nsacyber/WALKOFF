import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';
import { plainToClass } from 'class-transformer';

import { AppMetric } from '../models/metric/appMetric';
import { WorkflowMetric } from '../models/metric/workflowMetric';
// import { ActionMetric } from '../models/metric/actionMetric';

import { UtilitiesService } from '../utilities.service';

@Injectable()
export class MetricsService {
	constructor (private http: HttpClient, private utils: UtilitiesService) {}

	/**
	 * Gets an array of AppMetric objects specified in the DB.
	 */
	getAppMetrics(): Promise<AppMetric[]> {
		return this.http.get('api/metrics/apps')
			.toPromise()
			.then((res: any) => res.apps)
			.then((data) => plainToClass(AppMetric, data))
			.catch(this.utils.handleResponseError);
    }

    /**
	 * Gets an array of WorkflowMetric objects specified in the  DB.
	 */
	getWorkflowMetrics(): Promise<WorkflowMetric[]> {
		return this.http.get('api/metrics/workflows')
			.toPromise()
			.then((res: any) => res.workflows)
			.then((data) => plainToClass(WorkflowMetric, data))
			.catch(this.utils.handleResponseError);
	}
}
