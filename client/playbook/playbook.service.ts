import { Injectable } from '@angular/core';
import { Http, Response, Headers, RequestOptions } from '@angular/http';


@Injectable()
export class PlaybookService {
	requestOptions: RequestOptions;

	constructor (private http: Http) {
        let authKey = sessionStorage.getItem('authKey');
        if (authKey === null) {
          location.href = "/login";
        }
        let headers = new Headers({ 'Accept': 'application/json', 'Authentication-Token': authKey.toString()});
        this.requestOptions = new RequestOptions({ headers: headers });
	}
}
