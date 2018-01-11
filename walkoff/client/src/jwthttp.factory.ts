import { Http, RequestOptions, Response } from '@angular/http';
import { AuthConfig, tokenNotExpired } from 'angular2-jwt';
import { JwtConfigService, JwtHttp, RefreshConfig } from 'angular2-jwt-refresh';

export function GetJwtHttp(http: Http, options: RequestOptions) {
	const jwtOptions: RefreshConfig = {
		endPoint: '/api/auth/refresh',
		// optional
		// payload: { type: 'refresh' },
		beforeSeconds: 300, // refresh token before 5 min
		tokenName: 'refresh_token',
		refreshTokenGetter: (() => {
			const token = sessionStorage.getItem('refresh_token');

			if (token && tokenNotExpired(null, token)) { return token; }

			//TODO: figure out a better way of handling this... maybe incorporate login into the main component somehow
			location.href = '/login';
			return;
		}),
		tokenSetter: ((res: Response): boolean | Promise<void> => {
			res = res.json();

			if (!(res as any).access_token) {
				sessionStorage.removeItem('access_token');
				sessionStorage.removeItem('refresh_token');
				//TODO: figure out a better way of handling this... maybe incorporate login into the main component somehow
				location.href = '/login';
				return false;
			}

			sessionStorage.setItem('access_token', (res as any).access_token);
			// sessionStorage.setItem('refresh_token', (<any>res)['refresh_token']);

			return true;
		}),
	};

	const authConfig = new AuthConfig({
		noJwtError: true,
		// globalHeaders: [{ 'Accept': 'application/json' }],
		tokenName: 'access_token',
		tokenGetter: (() => sessionStorage.getItem('access_token')),
	});

	return new JwtHttp(
		new JwtConfigService(jwtOptions, authConfig),
		http,
		options,
	);
}
