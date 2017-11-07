import { Injectable } from '@angular/core';
import { Http, Response, Headers } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Device } from '../models/device';
import { DeviceApi } from '../models/api/deviceApi';
import { AppApi } from '../models/api/appApi';

@Injectable()
export class DevicesService {
	constructor (private authHttp: JwtHttp) {
	}

	getDevicesForApp(appName: string): Promise<Device[]> {
		return this.authHttp.get(`/api/apps/${appName}`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device[])
			.catch(this.handleError);
	}

	getAppDevice(appName: string, deviceName: string): Promise<Device> {
		return this.authHttp.get(`/api/apps/${appName}/devices/${deviceName}`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device)
			.catch(this.handleError);
	}

	getDevices(): Promise<Device[]> {
		return this.authHttp.get('/api/devices')
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device[])
			.catch(this.handleError);
	}

	addDevice(device: Device): Promise<Device> {
		return this.authHttp.put('/api/devices', device)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device)
			.catch(this.handleError);
	}

	editDevice(device: Device): Promise<Device> {
		return this.authHttp.post('/api/devices', device)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device)
			.catch(this.handleError);
	}

	deleteDevice(deviceId: number): Promise<void> {
		return this.authHttp.delete(`/api/devices/${deviceId}`)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	getDeviceApis(): Promise<AppApi[]> {
		return this.authHttp.get('api/apps/apis?field_name=device_types')
			.toPromise()
			.then(this.extractData)
			.then(data => data as AppApi[])
			// Clear out any apps without device apis
			.then(appApis => appApis.filter(a => a.device_apis && a.device_apis.length))
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
