import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { plainToClass, classToPlain } from 'class-transformer';

import { Global } from '../models/global';
import { AppApi } from '../models/api/appApi';
import { UtilitiesService } from '../utilities.service';
import { Observable, Subscriber } from 'rxjs';
import { Variable } from '../models/variable';

@Injectable({
	providedIn: 'root'
})
export class GlobalsService {

	globalsChange: Observable<any>;
	observer: Subscriber<any>;


	constructor (private http: HttpClient, private utils: UtilitiesService) {
		this.globalsChange = new Observable((observer) => {
            this.observer = observer;
            this.getAllGlobals().then(globals => this.observer.next(globals));
        })
	}

	emitChange(data: any) {
        if (this.observer) this.getAllGlobals().then(globals => this.observer.next(globals));
        return data;
    }

	/**
	 * Asynchronously returns an array of all existing globals from the server.
	 */
	getAllGlobals(): Promise<Variable[]> {
		return this.utils.paginateAll<Variable>(this.getGlobals.bind(this));
	}

	/**
	 * Asynchronously returns an array of existing globals from the server.
	 */
	getGlobals(page: number = 1): Promise<Variable[]> {
		return this.http.get(`api/globals/?page=${ page }`)
			.toPromise()
			.then((data) => plainToClass(Variable, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asynchronously sends a global to be added to the DB and returns the added global.
	 * @param global Global to add
	 */
	addGlobal(global: Variable): Promise<Variable> {
		return this.http.post('api/globals/', classToPlain(global))
			.toPromise()
			.then((data) => this.emitChange(data))
			.then((data) => plainToClass(Variable, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asynchronously sends a global to be updated within the DB and returns the edited global.
	 * @param global Global to edit
	 */
	editGlobal(global: Variable): Promise<Variable> {
		return this.http.put(`api/globals/${ global.id }`, classToPlain(global))
			.toPromise()
			.then((data) => this.emitChange(data))
			.then((data) => plainToClass(Variable, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asyncronously deletes a global from the DB and simply returns success.
	 * @param global Global to delete
	 */
	deleteGlobal(global: Variable): Promise<void> {
		return this.http.delete(`api/globals/${ global.id }`)
			.toPromise()
			.then((data) => this.emitChange(data))
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asynchronously returns a list of AppApi objects for all our loaded Apps.
	 * AppApi objects are scoped to only contain global apis.
	 */
	getGlobalApis(): Promise<AppApi[]> {
		return this.http.get('api/apps/apis/?field_name=device_apis')
			.toPromise()
			.then((data) => plainToClass(AppApi, data as Object[]))
			// Clear out any apps without global apis
			.then((appApis: AppApi[]) => appApis.filter(a => a.device_apis && a.device_apis.length))
			.catch(this.utils.handleResponseError);
	}
}
