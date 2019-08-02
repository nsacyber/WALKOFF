import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { plainToClass, classToPlain } from 'class-transformer';

import { Global } from '../models/global';
import { AppApi } from '../models/api/appApi';
import { UtilitiesService } from '../utilities.service';
import { Observable, Subscriber } from 'rxjs';
import { Variable } from '../models/variable';

import * as S3 from 'aws-sdk/clients/s3';

@Injectable({
	providedIn: 'root'
})
export class AppService {

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
		return this.http.get(`api/globals?page=${ page }`)
			.toPromise()
			.then((data) => plainToClass(Variable, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asynchronously sends a global to be added to the DB and returns the added global.
	 * @param global Global to add
	 */
	addGlobal(global: Variable): Promise<Variable> {
		return this.http.post('api/globals', classToPlain(global))
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
		return this.http.get('api/apps/apis?field_name=device_apis')
			.toPromise()
			.then((data) => plainToClass(AppApi, data as Object[]))
			// Clear out any apps without global apis
			.then((appApis: AppApi[]) => appApis.filter(a => a.device_apis && a.device_apis.length))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Gets all app apis from the server.
	 */
	getApis(): Promise<AppApi[]> {
		return this.http.get('api/apps/apis')
			.toPromise()
			.then((data: any[]) => plainToClass(AppApi, data))
			.then((appApis: AppApi[]) => {
				appApis.forEach(app => app.action_apis.map(action => {
					action.app_name = app.name;
					action.app_version = app.app_version;
					return action;
				}))
				return appApis;
			})
			.catch(this.utils.handleResponseError);
	}

	getApi(id: string): Promise<AppApi> {
		return this.getApis().then(apis => apis.find(api => api.id == id));
	}

	getFile(appApi: AppApi, path: string): Promise<string> {
		const Key = `apps/${ appApi.name }/${ appApi.app_version }/${ path }`;
		return this.getS3()
			.getObject({ Bucket: 'apps-bucket', Key})
			.promise()
			.then(data => data.Body.toString())
	}

	listFiles(appApi: AppApi) : Promise<any> {
		const Prefix = `apps/${ appApi.name }/${ appApi.app_version }/`;
		return this.getS3()
			.listObjectsV2({ Bucket: 'apps-bucket', Prefix})
			.promise()
			.then(data => data.Contents.map(c => c.Key.replace(Prefix, '')))
			.then(this.createTree);
	}

	createTree(files: string[]) {
		var tree = [];

		const sortTree = (a, b) => {
			if (a.folder == b.folder) return a.title.toLowerCase().localeCompare(b.title.toLowerCase());
			return a.folder ? -1 : 1;
		}

		files.map(file => {
			var arr = file.replace(/^\/|\/$/g, "").split('/');
			var parent = tree;
			for (let i = 0; i < arr.length; i++) {
				let node: any = { title: arr[i] };
				if ( i != arr.length - 1 ) {
					node.children = [];
					node.folder = true;
					node.expanded = true;
				}
				else {
					node.data = { path: file }
				}

				let curIndex = parent.findIndex(n => n.title == arr[i])
				if (curIndex < 0) curIndex = parent.push(node) - 1;

				if (parent[curIndex].folder) parent = parent[curIndex].children;

				parent.sort(sortTree)
			}   
		});

		tree.sort(sortTree);

		return tree;
	}

	getS3(): S3 {
		return new S3({
				accessKeyId: 'walkoff' ,
				secretAccessKey: 'walkoff123' ,
				endpoint: 'http://localhost:9001' ,
				s3ForcePathStyle: true, // needed with minio?
				signatureVersion: 'v4'
		});
	}

}
