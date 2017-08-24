import { Injectable } from '@angular/core';
import { Http, Response, Headers, RequestOptions } from '@angular/http';

import { Trigger } from '../models/trigger'

@Injectable()
export class TriggersService {
	requestOptions: RequestOptions;

	constructor (private http: Http) {
        let authKey = sessionStorage.getItem('authKey');
        if (authKey === null) {
          location.href = "/login";
        }
        let headers = new Headers({ 'Accept': 'application/json', 'Authentication-Token': authKey.toString()});
        this.requestOptions = new RequestOptions({ headers: headers });
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
