import { Injectable } from '@angular/core';
import { Response, Headers } from '@angular/http';
import { JwtHelper } from 'angular2-jwt';
import { JwtHttp } from 'angular2-jwt-refresh';

const REFRESH_TOKEN_NAME = 'refresh_token';
const ACCESS_TOKEN_NAME = 'access_token';

@Injectable()
export class AuthService {
	jwtHelper = new JwtHelper();

	constructor(private authHttp: JwtHttp) {
	}

	//TODO: not currently used, eventually should be used on the login
	login(username: string, password: string): Promise<void> {
		return this.authHttp.post('/api/auth', { username: username, password: password })
			.toPromise()
			.then(this.extractData)
			.then((tokens: { access_token: string, refresh_token: string }) => {
				sessionStorage.setItem(ACCESS_TOKEN_NAME, tokens.access_token);
				sessionStorage.setItem(REFRESH_TOKEN_NAME, tokens.refresh_token);
				location.href = '/';
			})
			.catch(this.handleError);
	}

	logout(): Promise<void> {
		return this.authHttp.post('/api/auth/logout', { refresh_token: sessionStorage.getItem(REFRESH_TOKEN_NAME) })
			.toPromise()
			.then(() => {
				this.clearTokens();
				location.href = '/login';
			})
			.catch(this.handleError);
	}

	clearTokens(): void {
		sessionStorage.removeItem(ACCESS_TOKEN_NAME);
		sessionStorage.removeItem(REFRESH_TOKEN_NAME);
	}

	//TODO: figure out how roles are going to be stored 
	canAccess(resource: string): boolean {
		let tokenInfo = this.getAndDecodeAccessToken();

		return false;
	}

	getRefreshToken(): string {
		return sessionStorage.getItem(REFRESH_TOKEN_NAME);
	}

	getAccessToken(): string {
		return sessionStorage.getItem(ACCESS_TOKEN_NAME);
	}

	getAndDecodeRefreshToken(): any {
		return this.jwtHelper.decodeToken(this.getRefreshToken());
	}

	getAndDecodeAccessToken(): any {
		return this.jwtHelper.decodeToken(this.getAccessToken());
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