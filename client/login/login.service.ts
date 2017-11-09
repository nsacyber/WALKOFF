import { Injectable } from '@angular/core';
import { Http, Response } from '@angular/http';

@Injectable()
export class LoginService {
	constructor (private http: Http) { }

	login(username: string, password: string): Promise<string> {
		return this.http.post('/login', { username, password })
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	private extractData (res: Response) {
		const body = res.json();
		return body.data || {};
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
