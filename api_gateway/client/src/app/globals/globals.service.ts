import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { plainToClass } from 'class-transformer';

import { Global } from '../models/global';
import { AppApi } from '../models/api/appApi';
import { UtilitiesService } from '../utilities.service';

@Injectable({
	providedIn: 'root'
})
export class GlobalsService {
	constructor (private http: HttpClient, private utils: UtilitiesService) {}

	/**
	 * Asynchronously returns an array of all existing globals from the server.
	 */
	getAllGlobals(): Promise<Global[]> {
		return this.utils.paginateAll<Global>(this.getGlobals.bind(this));
	}

	/**
	 * Asynchronously returns an array of existing globals from the server.
	 */
	getGlobals(page: number = 1): Promise<Global[]> {
		return this.http.get(`/api/devices?page=${ page }`)
			.toPromise()
			.then((data) => plainToClass(Global, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asynchronously sends a global to be added to the DB and returns the added global.
	 * @param global Global to add
	 */
	addGlobal(global: Global): Promise<Global> {
		return this.http.post('/api/devices', global)
			.toPromise()
			.then((data) => plainToClass(Global, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asynchronously sends a global to be updated within the DB and returns the edited global.
	 * @param global Global to edit
	 */
	editGlobal(global: Global): Promise<Global> {
		return this.http.patch('/api/devices', global)
			.toPromise()
			.then((data) => plainToClass(Global, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asyncronously deletes a global from the DB and simply returns success.
	 * @param globalId Global ID to delete
	 */
	deleteGlobal(globalId: number): Promise<void> {
		return this.http.delete(`/api/devices/${globalId}`)
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asynchronously returns a list of AppApi objects for all our loaded Apps.
	 * AppApi objects are scoped to only contain global apis.
	 */
	getGlobalApis(): Promise<AppApi[]> {
		return this.http.get('api/apps/apis?field_name=device_apis')
			.toPromise()
			.then((data) => plainToClass(AppApi, data as Object[]))
			// Clear out any apps without global apis
			.then((appApis: AppApi[]) => appApis.filter(a => a.device_apis && a.device_apis.length))
			.catch(this.utils.handleResponseError);
	}
}
