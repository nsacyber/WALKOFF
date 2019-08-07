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

	getFile(appApi: AppApi, file_path: string): Promise<string> {
		return this.http.post('/umpire/file', { app_name: appApi.name, app_version: appApi.app_version, file_path})
			.toPromise()
			.then(data => data as string)

		// const Key = `apps/${ appApi.name }/${ appApi.app_version }/${ file_path }`;
		// return this.getS3()
		// 	.getObject({ Bucket: 'apps-bucket', Key})
		// 	.promise()
		// 	.then(data => data.Body.toString())
	}

	putFile(appApi: AppApi, file_path: string, file_data: string): Promise<any> {
		return this.http.post('/umpire/file-upload', { app_name: appApi.name, app_version: appApi.app_version, file_path, file_data})
			.toPromise()

		// const Key = `apps/${ appApi.name }/${ appApi.app_version }/${ path }`;
		// return this.getS3()
		// 	.putObject({ Bucket: 'apps-bucket', Key, Body })
		// 	.promise()
		// 	.catch(e => console.log(e))
	}

	buildImage(appApi: AppApi): Promise<string> {
		return this.http.post('/umpire/build', { app_name: appApi.name, app_version: appApi.app_version })
			.toPromise()
			.then((data: any) => data.build_id)
	}

	listFiles(appApi: AppApi) : Promise<any> {
		return this.http.post('/umpire/files', { app_name: appApi.name, app_version: appApi.app_version })
			.toPromise()
			.then(this.createTree)


		// const Prefix = `apps/${ appApi.name }/${ appApi.app_version }/`;
		// return this.getS3()
		// 	.listObjectsV2({ Bucket: 'apps-bucket', Prefix})
		// 	.promise()
		// 	.then(data => data.Contents.map(c => c.Key.replace(Prefix, '')))
		// 	.then(this.createTree);
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

	// getS3(): S3 {
	// 	return new S3({
	// 			accessKeyId: 'walkoff' ,
	// 			secretAccessKey: 'walkoff123' ,
	// 			endpoint: 'http://localhost:9001' ,
	// 			s3ForcePathStyle: true, // needed with minio?
	// 			signatureVersion: 'v4'
	// 	});
	// }

}
