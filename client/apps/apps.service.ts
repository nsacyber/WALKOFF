import { Injectable } from '@angular/core';
import { Response, Headers } from '@angular/http';
import { JwtHelper } from 'angular2-jwt';
import { JwtHttp } from 'angular2-jwt-refresh';

const REFRESH_TOKEN_NAME = 'refresh_token';
const ACCESS_TOKEN_NAME = 'access_token';

@Injectable()
export class AuthService {
	constructor(private authHttp: JwtHttp) {}

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