import { Injectable } 			from '@angular/core';
import { Http, Response } 		from '@angular/http';

import { Observable }     from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';

import { AvailableSubscription } from './availableSubscription';
import { Case } from './case';

@Injectable()
export class ControllerService {
	constructor (private http: Http) { }

	getAvailableSubscriptions() : Promise<AvailableSubscription[]> {
		return this.http.get('/availablesubscriptions')
			.toPromise()
			.then(res => res.json().data as AvailableSubscription[])
			.catch(this.handleError);
	}

	getCases() : Promise<Case[]> {
		return this.http.get('/cases')
			.toPromise()
			.then(res => res.json().data as Case[])
			.catch(this.handleError);
	}

	addCase(name: String) : Promise<Case> {
		return this.http.put('/cases/' + name, {})
			.toPromise()
			.then(res => res.json().data as Case)
			.catch(this.handleError);
	}

	updateCase(editedCase: Case) : Promise<Case> {
		return this.http.post('/cases/' + name, editedCase)
			.toPromise()
			.then(res => res.json().data as Case)
			.catch(this.handleError);
	}

	removeCase(id: String) : Promise<void> {
		return this.http.delete('/cases/' + id)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	//TODO: route should most likely be GET
	executeWorkflow(playbook: string, workflow: string) : Promise<void> {
		return this.http.post('/playbooks/' + playbook + '/workflows/' + workflow + '/execute', {})
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getSchedulerStatus() : Promise<string> {
		return this.http.get('/execution/scheduler/')
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	//TODO: route should most likely be GET
	changeSchedulerStatus(status: string) : Promise<string> {
		return this.http.post('/execution/scheduler/' + status, {})
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	private extractData (res: Response) {
		let body = res.json();
		return body.data || {};
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
