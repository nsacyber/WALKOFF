import { Injectable } from '@angular/core';
import { JwtHttp } from 'angular2-jwt-refresh';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';
import { plainToClass } from 'class-transformer';

import { Case } from '../models/case/case';
import { CaseEvent } from '../models/case/caseEvent';
import { AvailableSubscription } from '../models/case/availableSubscription';
import { Playbook } from '../models/playbook/playbook';
import { UtilitiesService } from '../utilities.service';

@Injectable()
export class CasesService {
	constructor (private authHttp: JwtHttp, private utils: UtilitiesService) {}

	/**
	 * Gets an array of all Case objects specified in the cases DB.
	 */
	getAllCases(): Promise<Case[]> {
		return this.utils.paginateAll<Case>(this.getCases.bind(this));
	}

	/**
	 * Gets an array of Case objects specified in the cases DB.
	 */
	getCases(page: number = 1): Promise<Case[]> {
		return this.authHttp.get(`/api/cases?page=${ page }`)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object[]) => plainToClass(Case, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Gets an array of CaseEvents for a given case.
	 * @param caseId ID of case to query against.
	 */
	getEventsForCase(caseId: number): Promise<CaseEvent[]> {
		return this.authHttp.get(`/api/cases/${caseId}/events`)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object[]) => plainToClass(CaseEvent, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Adds a case represented by the caseToAdd specified.
	 * @param caseToAdd JSON of Case to add
	 */
	addCase(caseToAdd: Case): Promise<Case> {
		return this.authHttp.post('/api/cases', caseToAdd)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object) => plainToClass(Case, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Edits a case in place (by id specified within the Case JSON).
	 * @param caseToEdit JSON of Case to edit
	 */
	editCase(caseToEdit: Case): Promise<Case> {
		return this.authHttp.put('/api/cases', caseToEdit)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object) => plainToClass(Case, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Deletes a case by a given ID.
	 * @param id ID of Case to delete
	 */
	deleteCase(id: number): Promise<void> {
		return this.authHttp.delete(`/api/cases/${id}`)
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Gets a list of available event subscriptions for each type of object 
	 * to log against (controller, workflow, action, etc.);
	 */
	getAvailableSubscriptions(): Promise<AvailableSubscription[]> {
		return this.authHttp.get('/api/availablesubscriptions')
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object[]) => plainToClass(AvailableSubscription, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Gets a list of playbooks and all data within.
	 */
	getPlaybooks(): Promise<Playbook[]> {
		return this.authHttp.get('/api/playbooks?full=true')
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object[]) => plainToClass(Playbook, data))
			.catch(this.utils.handleResponseError);
	}
}
