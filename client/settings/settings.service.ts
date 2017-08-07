import { Injectable } from '@angular/core';
import { Http, Response, Headers, RequestOptions } from '@angular/http';

import { Configuration } from '../models/configuration'
import { User } from '../models/user'

@Injectable()
export class SettingsService {
	requestOptions: RequestOptions;

	constructor (private http: Http) {
		let authKey = localStorage.getItem('authKey');
		let headers = new Headers({ 'Accept': 'application/json' });
		headers.append('Authentication-Token', authKey);

		this.requestOptions = new RequestOptions({ headers: headers });
	}

	getConfiguration() : Promise<Configuration> {
		return this.http.get('/api/configuration', this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Configuration)
			.catch(this.handleError);
	};

	updateConfiguration(configuration: Configuration) : Promise<Configuration> {
		return this.http.post('/api/configuration', configuration, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Configuration)
			.catch(this.handleError);
	};

	getUsers() : Promise<User[]> {
		return this.http.get('/api/users', this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as User[])
			.catch(this.handleError);
	};

	addUser(user: User) : Promise<User> {
		return this.http.put('/api/users', user, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as User)
			.catch(this.handleError);
	}

	editUser(user: User) : Promise<User> {
		return this.http.post('/api/users', user, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as User)
			.catch(this.handleError);
	}

	deleteUser(id: number) : Promise<void> {
		return this.http.delete(`/api/users/${id}`, this.requestOptions)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}
	
	private extractData (res: Response) {
		let body = res.json();
		return body || {};
	}

	private handleError (error: Response | any) {
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
