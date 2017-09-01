import { Injectable } from '@angular/core';
import { Http, Response, Headers } from '@angular/http';

import { JwtHttp } from 'angular2-jwt-refresh';
import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';

import { Case } from '../models/case';
import { CaseEvent } from '../models/caseEvent';
import { AvailableSubscription } from '../models/availableSubscription';

@Injectable()
export class CasesService {
	constructor (private authHttp: JwtHttp) {
	}

	getCases() : Promise<Case[]> {
		return this.authHttp.get('/api/cases')
			.toPromise()
			.then(this.extractData)
			.then(data => data as Case[])
			.catch(this.handleError);
	}

	getEventsForCase(name: string) : Promise<CaseEvent[]> {
		return this.authHttp.get(`/cases/${name}/events`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as CaseEvent[])
			.catch(this.handleError);
	}

	addCase(caseToAdd: Case) : Promise<Case> {
		return this.authHttp.put('/api/cases', caseToAdd)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Case)
			.catch(this.handleError);
	}

	editCase(caseToEdit: Case) : Promise<Case> {
		return this.authHttp.post('/api/cases', caseToEdit)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Case)
			.catch(this.handleError);
	}

	deleteCase(id: number) : Promise<void> {
		return this.authHttp.delete(`/api/cases/${id}`)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getAvailableSubscriptions() : Promise<AvailableSubscription[]> {
		return this.authHttp.get('/api/availablesubscriptions')
			.toPromise()
			.then(this.extractData)
			.then(data => data as AvailableSubscription[])
			.catch(this.handleError);
	}

	getPlaybooks() : Promise<any> {
		return this.authHttp.get('/api/playbooks?full=true')
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
