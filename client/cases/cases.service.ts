import { Injectable } 			from '@angular/core';
import { Http, Headers, Response } 		from '@angular/http';

import { Observable }     from 'rxjs/Observable';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';

import { Case } from '../controller/case';

@Injectable()
export class CasesService {
	headers: Headers;
	authKey: string;

	constructor (private http: Http) {
	}

	getCases() : Promise<Case[]> {
		return this.http.get('/cases')
			.toPromise()
			.then(res => res.json().data as Case[])
			.catch(this.handleError);
	}

	getCaseSubscriptions() : Promise<Case[]> {
		return this.http.get('/cases/subscriptions')
			.toPromise()
			.then(res => res.json().data as Case[])
			.catch(this.handleError);
	}

	getEventsForCase(name: string) : Promise<Event[]> {
		return this.http.get('/cases/' + name + '/events')
			.toPromise()
			.then(res => res.json().data as Event[])
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
