<<<<<<< HEAD
import { Injectable } 			from '@angular/core';
import { Http, Headers, Response, RequestOptions } 		from '@angular/http';

import { Observable }     from 'rxjs/Observable';
=======
import { Injectable } from '@angular/core';
import { Http, Headers, Response } from '@angular/http';

import { JwtHttp } from 'angular2-jwt-refresh';
import { Observable } from 'rxjs/Observable';
>>>>>>> development
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';


@Injectable()
export class DashboardService {
<<<<<<< HEAD
	requestOptions : RequestOptions;

	constructor (private http: Http) {
		let authKey = localStorage.getItem('authKey');
		let headers = new Headers({ 'Accept': 'application/json' });
		headers.append('Authentication-Token', authKey);

		this.requestOptions = new RequestOptions({ headers: headers });
	}

	private handleError (error: Response | any) {
=======
	constructor (private http: Http) {
	}

	private handleError (error: Response | any): Promise<any> {
>>>>>>> development
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
