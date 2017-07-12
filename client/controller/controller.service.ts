import { Injectable } 			from '@angular/core';
import { Http, Headers, Response, RequestOptions } 		from '@angular/http';

import { Observable }     from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';

import { AvailableSubscription } from '../models/availableSubscription';
import { Case } from '../models/case';

interface IStringKeyObject {
	[key: string]: string;
};

const schedulerStatusNumberMapping: IStringKeyObject = {
	"0": "stopped",
	"1": "running",
	"2": "paused"
};

@Injectable()
export class ControllerService {
	requestOptions : RequestOptions;

	constructor (private http: Http) {
		let authKey = localStorage.getItem('authKey');
		let headers = new Headers({ 'Accept': 'application/json' });
		headers.append('Authentication-Token', authKey);

		this.requestOptions = new RequestOptions({ headers: headers });
	}

	getAvailableSubscriptions() : Promise<AvailableSubscription[]> {
		return this.http.get('/availablesubscriptions', this.requestOptions)
			.toPromise()
			.then(res => res.json().data as AvailableSubscription[])
			.catch(this.handleError);
	}

	getCases() : Promise<Case[]> {
		return this.http.get('/cases', this.requestOptions)
			.toPromise()
			.then(res => res.json().data as Case[])
			.catch(this.handleError);
	}

	addCase(name: String) : Promise<Case> {
		return this.http.put('/cases/' + name, {}, this.requestOptions)
			.toPromise()
			.then(res => res.json().data as Case)
			.catch(this.handleError);
	}

	updateCase(editedCase: Case) : Promise<Case> {
		return this.http.post('/cases/' + name, editedCase, this.requestOptions)
			.toPromise()
			.then(res => res.json().data as Case)
			.catch(this.handleError);
	}

	removeCase(id: String) : Promise<void> {
		return this.http.delete('/cases/' + id, this.requestOptions)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	//TODO: route should most likely be GET
	executeWorkflow(playbook: string, workflow: string) : Promise<void> {
		return this.http.post('/playbooks/' + playbook + '/workflows/' + workflow + '/execute', {}, this.requestOptions)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getSchedulerStatus() : Promise<string> {
		return this.http.get('/execution/scheduler', this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(statusObj => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.handleError);
	}

	//TODO: route should most likely be GET
	changeSchedulerStatus(status: string) : Promise<string> {
		return this.http.post('/execution/scheduler/' + status, {}, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(statusObj => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.handleError);
	}

	private extractData (res: Response) {
		let body = res.json();
		return body || {};
	}

	private handleError (error: Response | any) {
		let errMsg: string;
		if (error instanceof Response) {
			const body = error.json() || '';
			const err = body.error || JSON.stringify(body);
			errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
		} else {
			errMsg = error.message ? error.message : error.toString();
		}
		console.error(errMsg);
	}
}
