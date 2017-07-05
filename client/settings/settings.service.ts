import { Injectable } 			from '@angular/core';
import { Http, Response } 		from '@angular/http';

import { Configuration } from './configuration'

@Injectable()
export class SettingsService {
	constructor (private http: Http) { }

	getConfiguration() : Promise<Configuration> {
		return this.http.get('/configuration')
			.toPromise()
			.then(this.extractData)
			.then(data => data as Configuration)
			.catch(this.handleError);
	};

	updateConfiguration(configuration: Configuration) : Promise<Configuration> {
		console.log(configuration);
		return this.http.post('/configuration', configuration)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Configuration)
			.catch(this.handleError);
	}
	
	private extractData (res: Response) {
		let body = res.json();
		return body || {};
	}

	private handleError (error: Response | any) {
		let errMsg: string;
		if (error instanceof Response) {
			const body = error.json() || '';
			const err = body.error || JSON.stringify(body);
			errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
		} else {
			errMsg = error.message ? error.message : error.toString();
		}
		console.error(errMsg);
	}
}
