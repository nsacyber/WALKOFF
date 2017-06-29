import { Injectable } 			from '@angular/core';
import { Http, Response } 		from '@angular/http';

@Injectable()
export class SettingsService {
	constructor (private http: Http) { }

	getSettings() : Promise<string> {
		return this.http.get('/')
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	};
	
	doSomething() : Promise<string> {
		return Promise.resolve('hello');

		// return this.http.post('/login', {
		// 	username: username,
		// 	password: password
		// })
		// .map(this.extractData)
		// .catch(this.handleError);
	};

	private extractData (res: Response) {
		let body = res.json();
		return body.data || {};
	}

	private handleError (error: Response | any) {
		let errMsg: string;
		if (error instanceof Response) {
			const body = error.json() || '';
			const err = body.error || JSON.stringify(body);
			errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
		} else {
			errMsg = error.message ? error.message : error.toString();
		}
		console.error(errMsg);
	}
}
