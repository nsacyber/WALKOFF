import { Injectable } from '@angular/core';
import { Http, Response, Headers, RequestOptions } from '@angular/http';

import { Device } from '../models/device'

@Injectable()
export class DevicesService {
	requestOptions: RequestOptions;

	constructor (private http: Http) {
		let authKey = localStorage.getItem('authKey');
		let headers = new Headers({ 'Accept': 'application/json' });
		headers.append('Authentication-Token', authKey);

		this.requestOptions = new RequestOptions({ headers: headers });
	}

	getDevicesForApp(appName: string) : Promise<Device[]> {
		return this.http.get(`/api/apps/${appName}`, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device[])
			.catch(this.handleError);
	}

	getAppDevice(appName: string, deviceName: string) : Promise<Device> {
		return this.http.get(`/api/apps/${appName}/devices/${deviceName}`, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device)
			.catch(this.handleError);
	}

	getDevices() : Promise<Device[]> {
		return this.http.get(`/api/devices`, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device[])
			.catch(this.handleError);
	}

	addDevice(device: Device) : Promise<Device> {
		return this.http.put(`/api/devices`, device, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device)
			.catch(this.handleError);
	}

	editDevice(device: Device) : Promise<Device> {
		return this.http.post(`/api/devices`, device, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device)
			.catch(this.handleError);
	}

	deleteDevice(deviceId: number) : Promise<void> {
		return this.http.delete(`/api/devices/${deviceId}`, this.requestOptions)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getApps() : Promise<string[]> {
		return this.http.get(`/api/apps`, this.requestOptions)
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
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
