import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { plainToClass } from 'class-transformer';

import { Configuration } from '../models/configuration';
import { User } from '../models/user';
import { Role } from '../models/role';
import { AvailableResourceAction } from '../models/availableResourceAction';
import { UtilitiesService } from '../utilities.service';

@Injectable({
	providedIn: 'root'
})
export class SettingsService {
	constructor (private http: HttpClient, private utils: UtilitiesService) {}

	getConfiguration(): Promise<Configuration> {
		return this.http.get('api/settings/')
			.toPromise()
			.then((data: object) => plainToClass(Configuration, data))
			.catch(this.utils.handleResponseError);
	}

	updateConfiguration(configuration: Configuration): Promise<Configuration> {
		return this.http.put('api/settings/', configuration)
			.toPromise()
			.then((data: object) => plainToClass(Configuration, data))
			.catch(this.utils.handleResponseError);
	}

	getAllUsers(): Promise<User[]> {
		return this.utils.paginateAll<User>(this.getUsers.bind(this));
	}

	getUsers(page: number = 1): Promise<User[]> {
		return this.http.get(`api/users/?page=${ page }`)
			.toPromise()
			.then((data: object[]) => plainToClass(User, data))
			.catch(this.utils.handleResponseError);
	}

	addUser(user: User): Promise<User> {
		return this.http.post('api/users/', user)
			.toPromise()
			.then((data: object) => plainToClass(User, data))
			.catch(this.utils.handleResponseError);
	}

	editUser(user: User): Promise<User> {
		return this.http.put(`api/users/${user.id}`, user)
			.toPromise()
			.then((data: object) => plainToClass(User, data))
			.catch(this.utils.handleResponseError);
	}

	deleteUser(id: number): Promise<void> {
		return this.http.delete(`api/users/${id}`)
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	getRoles(): Promise<Role[]> {
		return this.http.get('api/roles/')
			.toPromise()
			.then((data: object[]) => plainToClass(Role, data))
			.catch(this.utils.handleResponseError);
	}

	addRole(role: Role): Promise<Role> {
		return this.http.post('api/roles/', role)
			.toPromise()
			.then((data: object) => plainToClass(Role, data))
			.catch(this.utils.handleResponseError);
	}

	editRole(role: Role): Promise<Role> {
		return this.http.put(`api/roles/${role.id}`, role)
			.toPromise()
			.then((data: object) => plainToClass(Role, data))
			.catch(this.utils.handleResponseError);
	}

	deleteRole(id: string): Promise<void> {
		return this.http.delete(`api/roles/${id}`)
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
		return this.http.get('api/roles/availableresourceactions/')
			.toPromise()
			.then((data: object[]) => plainToClass(AvailableResourceAction, data))
			.catch(this.utils.handleResponseError);
	}
}
