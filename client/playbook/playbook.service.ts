import { Injectable } from '@angular/core';
import { Http, Response, Headers, RequestOptions } from '@angular/http';


@Injectable()
export class PlaybookService {
	requestOptions: RequestOptions;

	constructor (private http: Http) {
//		let authKey = localStorage.getItem('authKey');
		let headers = new Headers({ 'Accept': 'application/json' });
//		headers.append('Authentication-Token', authKey);


		this.requestOptions = new RequestOptions({ headers: headers, withCredentials: true });
	}
}
