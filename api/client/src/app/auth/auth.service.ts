import { Injectable } from '@angular/core';
import { JwtHelperService } from '@auth0/angular-jwt';
import { HttpClient } from '@angular/common/http';
import { plainToClass } from 'class-transformer';

import { AccessToken } from '../models/accessToken';
import { UtilitiesService } from '../utilities.service';

const REFRESH_TOKEN_NAME = 'refresh_token';
const ACCESS_TOKEN_NAME = 'access_token';

declare var EventSourcePolyfill: any;

@Injectable()
export class AuthService {

	jwtHelper = new JwtHelperService();

	constructor(private http: HttpClient, private utils: UtilitiesService) {}

	//TODO: not currently used, eventually should be used on the login
	login(username: string, password: string): Promise<void> {
		return this.http.post('api/auth', { username, password })
			.toPromise()
			.then((tokens: { access_token: string, refresh_token: string }) => {
				sessionStorage.setItem(ACCESS_TOKEN_NAME, tokens.access_token);
				sessionStorage.setItem(REFRESH_TOKEN_NAME, tokens.refresh_token);
				// location.href = '/';
			})
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Logs the user out on the server and clears the tokens in session storage.
	 */
	logout(): Promise<void> {
		const headers = { 'Authorization': `Bearer ${ this.getAccessToken() }` };

		return this.http.post('api/auth/logout', { refresh_token: sessionStorage.getItem(REFRESH_TOKEN_NAME) }, { headers })
			.toPromise()
			.then(() => {
				this.clearTokens();
			})
			.catch(this.utils.handleResponseError);
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
	 * Returns true if access token is expired
	 */
	isAccessTokenExpired(): boolean {
		return this.getAccessToken() && this.jwtHelper.isTokenExpired(this.getAccessToken())
	}

	/**
	 * Returns true is refresh token is expired
	 */
	isRefreshTokenExpired(): boolean {
		return this.getRefreshToken() && this.jwtHelper.isTokenExpired(this.getRefreshToken())
	}

	/**
	 * Asynchronously checks if the access token needs to be refreshed, and refreshes it if necessary.
	 * Will return a promise of the existing access token or the newly refreshed access token.
	 */
	getAccessTokenRefreshed(): Promise<string> {
		if (!this.isAccessTokenExpired()) return Promise.resolve(this.getAccessToken());

		if (this.isRefreshTokenExpired()) {
			sessionStorage.removeItem('access_token');
			sessionStorage.removeItem('refresh_token');
			//TODO: figure out a better way of handling this... maybe incorporate login into the main component somehow
			location.href = 'login';
			return Promise.reject('Refresh token does not exist or has expired. Please log in again.');
		}

		const headers = { 'Authorization': `Bearer ${ this.getRefreshToken() }` };

		return this.http.post('api/auth/refresh', {}, { headers })
			.toPromise()
			.then((res: any) => {
				const accessToken = res.access_token;
				sessionStorage.setItem('access_token', accessToken);
				return accessToken;
			})
			.catch(this.utils.handleResponseError);
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

	getEventSource(url): Promise<any> {
		//return Promise.resolve(new AuthEventSource(url, this));
		return this.getAccessTokenRefreshed().then(authToken => {
			let eventSource = new EventSourcePolyfill(url, { headers: { 'Authorization': `Bearer ${ authToken }` }})
			eventSource.onerror = (err: Error) => console.error(err);
			return eventSource;
		});
	}
}


// export class AuthEventSource {
// 	eventSource: any;
// 	timeout: any;
// 	listeners: any[] = [];
// 	errorHandler: any = (err: Error) => console.error(err);

// 	constructor(private url, private authService: AuthService) {
// 		this._create();
// 	}

// 	private _getConfig() {
// 		return this.authService.getAccessTokenRefreshed().then(authToken => ({ headers: { 'Authorization': `Bearer ${ authToken }` }}));
// 	}

// 	private _create() {
// 		this._getConfig().then(config => {
// 			this.eventSource = new EventSourcePolyfill(this.url, config);
// 			this.eventSource.onopen = (e) => this._restartTimeout();
// 			this.eventSource.onmessage = (e) => this._restartTimeout();
// 			this.eventSource.onerror = this.errorHandler;
// 			this.listeners.forEach(listener => this.eventSource.addEventListener(listener.event, listener.handler));
// 		})
// 	}

// 	private _restartTimeout() {
// 		console.log('restarting timer');
// 		if (this.timeout) clearTimeout(this.timeout);
// 		this.timeout = setTimeout(() => {
// 			console.log(`Restarting EventSource: ${ this.url }`)
// 			this.close();
// 			this._create();
// 		}, 30000)
// 	}

// 	addEventListener(event, handler) {
// 		this.listeners.push({ event, handler })
// 		if (this.eventSource) this.eventSource.addEventListener(event, handler);
// 	}

// 	onerror(handler) {
// 		this.errorHandler = handler;
// 		if (this.eventSource) this.eventSource.onerror = handler;
// 	}

// 	close() {
// 		if (this.timeout) clearTimeout(this.timeout);
// 		if (this.eventSource) this.eventSource.close();
// 	}
// }
