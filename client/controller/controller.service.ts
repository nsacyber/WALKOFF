import { Injectable } 			from '@angular/core';
import { Http, Headers, Response } 		from '@angular/http';

import { Observable }     from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';

import { AvailableSubscription } from './availableSubscription';
import { Case } from './case';

const schedulerStatusNumberMapping: Object = {
	"0": "stopped",
	"1": "running",
	"2": "paused"
};

@Injectable()
export class ControllerService {

	headers: Headers;
	authKey: string;

	constructor (private http: Http) {
		// this.authKey = Window.authkey;
		// console.log(this.authKey);
		// this.headers = new Headers();
		// this.headers.append('Authentication-Token', this.authKey);
	}

	getAvailableSubscriptions() : Promise<AvailableSubscription[]> {
		return this.http.get('/availablesubscriptions', this.headers)
			.toPromise()
			.then(res => res.json().data as AvailableSubscription[])
			.catch(this.handleError);
	}

	getCases() : Promise<Case[]> {
		let headers = new Headers;
		headers.append('Authentication-Token', this.authKey);
		return this.http.get('/cases', { headers: headers })
			.toPromise()
			.then(res => res.json().data as Case[])
			.catch(this.handleError);
	}

	addCase(name: String) : Promise<Case> {
		return this.http.put('/cases/' + name, {}, this.headers)
			.toPromise()
			.then(res => res.json().data as Case)
			.catch(this.handleError);
	}

	updateCase(editedCase: Case) : Promise<Case> {
		return this.http.post('/cases/' + name, editedCase, this.headers)
			.toPromise()
			.then(res => res.json().data as Case)
			.catch(this.handleError);
	}

	removeCase(id: String) : Promise<void> {
		return this.http.delete('/cases/' + id, this.headers)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	//TODO: route should most likely be GET
	executeWorkflow(playbook: string, workflow: string) : Promise<void> {
		return this.http.post('/playbooks/' + playbook + '/workflows/' + workflow + '/execute', {}, this.headers)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getSchedulerStatus() : Promise<string> {
		return this.http.get('/execution/scheduler/', this.headers)
			.toPromise()
			.then(this.extractData)
			.then(statusObj => schedulerStatusNumberMapping[statusObj.status])
			.catch(this.handleError);
	}

	//TODO: route should most likely be GET
	changeSchedulerStatus(status: string) : Promise<string> {
		return this.http.post('/execution/scheduler/' + status, {}, this.headers)
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
