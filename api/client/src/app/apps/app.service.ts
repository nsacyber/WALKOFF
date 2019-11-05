import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { plainToClass } from 'class-transformer';

import { AppApi } from '../models/api/appApi';
import { UtilitiesService } from '../utilities.service';

// import * as S3 from 'aws-sdk/clients/s3';

@Injectable({
	providedIn: 'root'
})
export class AppService {

	constructor (private http: HttpClient, private utils: UtilitiesService) { }

	/**
	 * Gets all app apis from the server.
	 */
	getApis(): Promise<AppApi[]> {
		return this.http.get('api/apps/apis/')
			.toPromise()
			.then((data: any[]) => plainToClass(AppApi, data))
			.then((appApis: AppApi[]) => appApis.filter(a => a.name !== 'Builtin'))
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

	getFile(appApi: AppApi, file_path: string): Promise<string> {
		return this.http.get(`api/umpire/file/${ appApi.name }/${ appApi.app_version }`, { params: { file_path }})
			.toPromise()
			.then(data => data as string)
	}

	putFile(appApi: AppApi, file_path: string, file_data: string): Promise<any> {
		return this.http.post('api/umpire/file_upload', { app_name: appApi.name, app_version: appApi.app_version, file_path, file_data})
			.toPromise()
	}

	buildImage(appApi: AppApi): Promise<string> {
		return this.http.post(`api/umpire/build/${ appApi.name }/${ appApi.app_version }`, { app_name: appApi.name, app_version: appApi.app_version })
			.toPromise()
			.then((data: any) => data.build_id)
	}

	buildStatus() {
		return this.http.get(`api/umpire/build`)
			.toPromise()
			.then(console.log)
	}

	listFiles(appApi: AppApi) : Promise<any> {
		return this.http.get(`api/umpire/files/${ appApi.name }/${ appApi.app_version }`)
			.toPromise()
			.then(files => (files as string[]).concat('').map(f => 'root/' + f))
			.then(this.createTree)
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
					node.data = { path: arr.slice(1, i + 1).concat('').join('/') }
				}
				else {
					node.data = { path: arr.slice(1).join('/') }
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
}
