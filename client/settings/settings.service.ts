import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Configuration } from '../models/configuration';
import { User } from '../models/user';
import { Role } from '../models/role';
import { AvailableResourceAction } from '../models/availableResourceAction';

@Injectable()
export class SettingsService {
	constructor (private authHttp: JwtHttp) {
	}

	getConfiguration(): Promise<Configuration> {
		return this.authHttp.get('/api/configuration')
			.toPromise()
			.then(this.extractData)
			.then(data => data as Configuration)
			.catch(this.handleError);
	}

	updateConfiguration(configuration: Configuration): Promise<Configuration> {
		return this.authHttp.post('/api/configuration', configuration)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Configuration)
			.catch(this.handleError);
	}

	getUsers(): Promise<User[]> {
		return this.authHttp.get('/api/users')
			.toPromise()
			.then(this.extractData)
			.then(data => data as User[])
			.catch(this.handleError);
	}

	addUser(user: User): Promise<User> {
		return this.authHttp.put('/api/users', user)
			.toPromise()
			.then(this.extractData)
			.then(data => data as User)
			.catch(this.handleError);
	}

	editUser(user: User): Promise<User> {
		return this.authHttp.post('/api/users', user)
			.toPromise()
			.then(this.extractData)
			.then(data => data as User)
			.catch(this.handleError);
	}

	deleteUser(id: number): Promise<void> {
		return this.authHttp.delete(`/api/users/${id}`)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getRoles(): Promise<Role[]> {
		return this.authHttp.get('/api/roles')
			.toPromise()
			.then(this.extractData)
			.then(data => data as Role[])
			.catch(this.handleError);
	}

	addRole(role: Role): Promise<Role> {
		return this.authHttp.put('/api/roles', role)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Role)
			.catch(this.handleError);
	}

	editRole(role: Role): Promise<Role> {
		return this.authHttp.post('/api/roles', role)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Role)
			.catch(this.handleError);
	}

	deleteRole(id: number): Promise<void> {
		return this.authHttp.delete(`/api/roles/${id}`)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getAvailableResourceActions(): Promise<AvailableResourceAction[]> {
		// const testData: AvailableResourceAction[] = [
		// 	{
		// 		name: 'workflow',
		// 		actions: [ 'create', 'read', 'update', 'delete', 'execute' ],
		// 	},
		// 	{
		// 		name: 'device',
		// 		actions: [ 'create', 'read', 'update', 'delete', 'import', 'export' ],
		// 	},
		// 	{
		// 		name: 'user',
		// 		actions: [ 'create', 'read', 'update', 'delete' ],
		// 	},
		// 	{
		// 		name: 'case',
		// 		actions: [ 'create', 'read', 'update', 'delete' ],
		// 	},
		// 	{
		// 		name: 'test',
		// 		actions: ['some', 'actions', 'go', 'here'],
		// 		app_name: 'Utilities',
		// 	},
		// ];

		// return Promise.resolve(testData);
		return this.authHttp.get('/api/availableresourceactions')
			.toPromise()
			.then(this.extractData)
			.then(data => data as AvailableResourceAction[])
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
