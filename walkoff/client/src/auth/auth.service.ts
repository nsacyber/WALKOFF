import { Injectable } from '@angular/core';
import { Http, Response, Headers } from '@angular/http';
import { JwtHelper } from 'angular2-jwt';
import { JwtHttp } from 'angular2-jwt-refresh';
import { plainToClass } from 'class-transformer';

import { AccessToken } from '../models/accessToken';

const REFRESH_TOKEN_NAME = 'refresh_token';
const ACCESS_TOKEN_NAME = 'access_token';

@Injectable()
export class AuthService {
	jwtHelper = new JwtHelper();

	constructor(private authHttp: JwtHttp, private http: Http) {
	}

	//TODO: not currently used, eventually should be used on the login
	login(username: string, password: string): Promise<void> {
		return this.authHttp.post('/api/auth', { username, password })
			.toPromise()
			.then(this.extractData)
			.then((tokens: { access_token: string, refresh_token: string }) => {
				sessionStorage.setItem(ACCESS_TOKEN_NAME, tokens.access_token);
				sessionStorage.setItem(REFRESH_TOKEN_NAME, tokens.refresh_token);
				location.href = '/';
			})
			.catch(this.handleError);
	}

	/**
	 * Logs the user out on the server and clears the tokens in session storage.
	 */
	logout(): Promise<void> {
		return this.authHttp.post('/api/auth/logout', { refresh_token: sessionStorage.getItem(REFRESH_TOKEN_NAME) })
			.toPromise()
			.then(() => {
				this.clearTokens();
			})
			.catch(this.handleError);
	}

	/**
	 * Clears our JWTs from session storage. Used when logging out.
	 */
	clearTokens(): void {
		sessionStorage.removeItem(ACCESS_TOKEN_NAME);
		sessionStorage.removeItem(REFRESH_TOKEN_NAME);
	}

	//TODO: figure out how roles are going to be stored
	//stub method until we figure out how we're going to handle client side authorization stuff.
	canAccess(resourceName: string, actionName: string): boolean {
		return false;
	}

	/**
	 * Grabs the refresh JWT string from session storage.
	 */
	getRefreshToken(): string {
		return sessionStorage.getItem(REFRESH_TOKEN_NAME);
	}

	/**
	 * Grabs the access JWT string from session storage.
	 */
	getAccessToken(): string {
		return sessionStorage.getItem(ACCESS_TOKEN_NAME);
	}

	/**
	 * Asynchronously checks if the access token needs to be refreshed, and refreshes it if necessary.
	 * Will return a promise of the existing access token or the newly refreshed access token.
	 */
	getAccessTokenRefreshed(): Promise<string> {
		const token = this.getAccessToken();
		if (!this.jwtHelper.isTokenExpired(token)) { return Promise.resolve(token); }
		const refreshToken = this.getRefreshToken();

		if (!refreshToken || this.jwtHelper.isTokenExpired(refreshToken)) {
			return Promise.reject('Refresh token does not exist or has expired. Please log in again.');
		}

		const headers = new Headers({ Authorization: `Bearer ${this.getRefreshToken()}` });
		return this.http.post('/api/auth/refresh', {}, { headers })
			.toPromise()
			.then(this.extractData)
			.then(refreshedToken => refreshedToken.access_token)
			.catch(this.handleError);
	}

	/**
	 * Returns an AccessToken object, decoded from the refresh token in session storage.
	 */
	getAndDecodeRefreshToken(): AccessToken {
		return plainToClass(AccessToken, (this.jwtHelper.decodeToken(this.getRefreshToken()) as object));
	}

	/**
	 * Returns an AccessToken object, decoded from the access token in session storage.
	 */
	getAndDecodeAccessToken(): AccessToken {
		return plainToClass(AccessToken, (this.jwtHelper.decodeToken(this.getAccessToken()) as object));
	}

	/**
	 * Checks if the access token is 'fresh'.
	 * Freshness is determined if this is the access token from our actual authentication,
	 * or if it is a token that was supplied using the /api/auth/refresh endpoint.
	 */
	isAccessTokenFresh(): boolean {
		return !!this.getAndDecodeAccessToken().fresh;
	}

	private extractData(res: Response) {
		const body = res.json();
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
