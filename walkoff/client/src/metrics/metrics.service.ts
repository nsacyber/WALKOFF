import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';
import { plainToClass } from 'class-transformer';

import { AppMetric } from '../models/metric/appMetric';
import { WorkflowMetric } from '../models/metric/workflowMetric';
// import { ActionMetric } from '../models/metric/actionMetric';

@Injectable()
export class MetricsService {
	constructor (private authHttp: JwtHttp) {
	}

	/**
	 * Gets an array of AppMetric objects specified in the DB.
	 */
	getAppMetrics(): Promise<AppMetric[]> {
		return this.authHttp.get('/api/metrics/apps')
			.toPromise()
			.then(this.extractData)
			.then((data) => plainToClass(AppMetric, data.apps))
			.catch(this.handleError);
    }
    
    /**
	 * Gets an array of WorkflowMetric objects specified in the  DB.
	 */
	getWorkflowMetrics(): Promise<WorkflowMetric[]> {
		return this.authHttp.get('/api/metrics/workflows')
			.toPromise()
			.then(this.extractData)
			.then((data) => plainToClass(WorkflowMetric, data.workflows))
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
