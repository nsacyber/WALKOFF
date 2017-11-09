import { Injectable } from '@angular/core';
import { Response } from '@angular/http';

import { JwtHttp } from 'angular2-jwt-refresh';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';

@Injectable()
export class DashboardService {
	constructor (private authHttp: JwtHttp) {}

	getDashboard(name: string) {
		return this.authHttp.get(`/api/dashboard/${name}`)
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	private extractData (res: Response) {
		const body = res.json();
		return body || {};
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
