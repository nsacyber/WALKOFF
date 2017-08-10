import { Injectable } from '@angular/core';
import { Http, Response, Headers, RequestOptions } from '@angular/http';

import { Observable } from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';

import { Case } from '../models/case';
import { CaseEvent } from '../models/caseEvent';

@Injectable()
export class CasesService {
	requestOptions: RequestOptions;

	constructor (private http: Http) {
		let authKey = localStorage.getItem('authKey');
		let headers = new Headers({ 'Accept': 'application/json' });
		headers.append('Authentication-Token', authKey);

		this.requestOptions = new RequestOptions({ headers: headers });
	}

	getCases() : Promise<Case[]> {
		return this.http.get('/api/cases', this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Case[])
			.catch(this.handleError);
	}

	getCaseSubscriptions() : Promise<Case[]> {
		return this.http.get('/api/cases/subscriptions', this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Case[])
			.catch(this.handleError);
	}

	getEventsForCase(name: string) : Promise<CaseEvent[]> {
		return this.http.get(`/cases/${name}/events`, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as CaseEvent[])
			.catch(this.handleError);
	}

	addCase(caseToAdd: Case) : Promise<Case> {
		return this.http.put('/api/cases', caseToAdd, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Case)
			.catch(this.handleError);
	}

	editCase(caseToEdit: Case) : Promise<Case> {
		return this.http.post('/api/cases', caseToEdit, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Case)
			.catch(this.handleError);
	}

	deleteCase(id: number) : Promise<void> {
		return this.http.delete(`/api/cases/${id}`, this.requestOptions)
			.toPromise()
			.then(() => null)
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
