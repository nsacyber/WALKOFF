import { Injectable } from '@angular/core';
import { Response } from '@angular/http';

import { JwtHttp } from 'angular2-jwt-refresh';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';

import { Case } from '../models/case/case';
import { CaseEvent } from '../models/case/caseEvent';
import { AvailableSubscription } from '../models/case/availableSubscription';
import { Playbook } from '../models/playbook/playbook';

@Injectable()
export class CasesService {
	constructor (private authHttp: JwtHttp) {
	}

	/**
	 * Gets an array of Case objects specified in the cases DB.
	 */
	getCases(): Promise<Case[]> {
		return this.authHttp.get('/api/cases')
			.toPromise()
			.then(this.extractData)
			.then(data => data as Case[])
			.catch(this.handleError);
	}

	/**
	 * Gets an array of CaseEvents for a given case.
	 * @param caseId ID of case to query against.
	 */
	getEventsForCase(caseId: number): Promise<CaseEvent[]> {
		return this.authHttp.get(`/api/cases/${caseId}/events`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as CaseEvent[])
			.catch(this.handleError);
	}

	/**
	 * Adds a case represented by the caseToAdd specified.
	 * @param caseToAdd JSON of Case to add
	 */
	addCase(caseToAdd: Case): Promise<Case> {
		return this.authHttp.post('/api/cases', caseToAdd)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Case)
			.catch(this.handleError);
	}

	/**
	 * Edits a case in place (by id specified within the Case JSON).
	 * @param caseToEdit JSON of Case to edit
	 */
	editCase(caseToEdit: Case): Promise<Case> {
		return this.authHttp.put('/api/cases', caseToEdit)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Case)
			.catch(this.handleError);
	}

	/**
	 * Deletes a case by a given ID.
	 * @param id ID of Case to delete
	 */
	deleteCase(id: number): Promise<void> {
		return this.authHttp.delete(`/api/cases/${id}`)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	/**
	 * Gets a list of available event subscriptions for each type of object 
	 * to log against (controller, workflow, action, etc.);
	 */
	getAvailableSubscriptions(): Promise<AvailableSubscription[]> {
		return this.authHttp.get('/api/availablesubscriptions')
			.toPromise()
			.then(this.extractData)
			.then(data => data as AvailableSubscription[])
			.catch(this.handleError);
	}

	/**
	 * Gets a list of playbooks and all data within.
	 */
	getPlaybooks(): Promise<Playbook[]> {
		return this.authHttp.get('/api/playbooks?full=true')
			.toPromise()
			.then(this.extractData)
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
