import { Injectable } from '@angular/core';
import { Response, Headers } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

@Injectable()
export class AuthService {
	constructor(private authHttp: JwtHttp) {
	}

	logout(): Promise<void> {
		return this.authHttp.post('/api/auth/logout', { refresh_token: localStorage.getItem('refresh_token') })
			.toPromise()
			.then(() => {
				location.href = '/login';
			})
			.catch(this.handleError);
	}

	getToken(): Promise<string> {
		return this.authHttp.get('/api/auth/token')
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	private extractData(res: Response) {
		let body = res.json();
		return body || {};
	}

	private handleError(error: Response | any): Promise<any> {
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