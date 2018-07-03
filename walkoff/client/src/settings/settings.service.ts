import { Injectable } from '@angular/core';
import { JwtHttp } from 'angular2-jwt-refresh';
import { plainToClass } from 'class-transformer';

import { Configuration } from '../models/configuration';
import { User } from '../models/user';
import { Role } from '../models/role';
import { AvailableResourceAction } from '../models/availableResourceAction';
import { UtilitiesService } from '../utilities.service';

@Injectable()
export class SettingsService {
	constructor (private authHttp: JwtHttp, private utils: UtilitiesService) {}

	getConfiguration(): Promise<Configuration> {
		return this.authHttp.get('/api/configuration')
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object) => plainToClass(Configuration, data))
			.catch(this.utils.handleResponseError);
	}

	updateConfiguration(configuration: Configuration): Promise<Configuration> {
		return this.authHttp.put('/api/configuration', configuration)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object) => plainToClass(Configuration, data))
			.catch(this.utils.handleResponseError);
	}

	getAllUsers(): Promise<User[]> {
		return this.utils.paginateAll<User>(this.getUsers.bind(this));
	}

	getUsers(page: number = 1): Promise<User[]> {
		return this.authHttp.get(`/api/users?page=${ page }`)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object[]) => plainToClass(User, data))
			.catch(this.utils.handleResponseError);
	}

	addUser(user: User): Promise<User> {
		return this.authHttp.post('/api/users', user)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object) => plainToClass(User, data))
			.catch(this.utils.handleResponseError);
	}

	editUser(user: User): Promise<User> {
		return this.authHttp.put('/api/users', user)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object) => plainToClass(User, data))
			.catch(this.utils.handleResponseError);
	}

	deleteUser(id: number): Promise<void> {
		return this.authHttp.delete(`/api/users/${id}`)
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	getRoles(): Promise<Role[]> {
		return this.authHttp.get('/api/roles')
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object[]) => plainToClass(Role, data))
			.catch(this.utils.handleResponseError);
	}

	addRole(role: Role): Promise<Role> {
		return this.authHttp.post('/api/roles', role)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object) => plainToClass(Role, data))
			.catch(this.utils.handleResponseError);
	}

	editRole(role: Role): Promise<Role> {
		return this.authHttp.put('/api/roles', role)
			.toPromise()
			.then(this.utils.extractResponseData)
			.then((data: object) => plainToClass(Role, data))
			.catch(this.utils.handleResponseError);
	}

	deleteRole(id: number): Promise<void> {
		return this.authHttp.delete(`/api/roles/${id}`)
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
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
			.then(this.utils.extractResponseData)
			.then((data: object[]) => plainToClass(AvailableResourceAction, data))
			.catch(this.utils.handleResponseError);
	}
}
