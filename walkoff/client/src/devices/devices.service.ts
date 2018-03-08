import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';
import { plainToClass } from 'class-transformer';

import { Device } from '../models/device';
import { AppApi } from '../models/api/appApi';

@Injectable()
export class DevicesService {
	constructor (private authHttp: JwtHttp) {
	}

	/**
	 * Asynchronously returns an array of all existing devices from the server.
	 */
	getDevices(): Promise<Device[]> {
		return this.authHttp.get('/api/devices')
			.toPromise()
			.then(this.extractData)
			.then((data: object[]) => plainToClass(Device, data))
			.catch(this.handleError);
	}

	/**
	 * Asynchronously sends a device to be added to the DB and returns the added device.
	 * @param device Device to add
	 */
	addDevice(device: Device): Promise<Device> {
		return this.authHttp.post('/api/devices', device)
			.toPromise()
			.then(this.extractData)
			.then((data: object) => plainToClass(Device, data))
			.catch(this.handleError);
	}

	/**
	 * Asynchronously sends a device to be updated within the DB and returns the edited device.
	 * @param device Device to edit
	 */
	editDevice(device: Device): Promise<Device> {
		return this.authHttp.put('/api/devices', device)
			.toPromise()
			.then(this.extractData)
			.then((data: object) => plainToClass(Device, data))
			.catch(this.handleError);
	}

	/**
	 * Asyncronously deletes a device from the DB and simply returns success.
	 * @param deviceId Device ID to delete
	 */
	deleteDevice(deviceId: number): Promise<void> {
		return this.authHttp.delete(`/api/devices/${deviceId}`)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	/**
	 * Asynchronously returns a list of AppApi objects for all our loaded Apps.
	 * AppApi objects are scoped to only contain device apis.
	 */
	getDeviceApis(): Promise<AppApi[]> {
		return this.authHttp.get('api/apps/apis?field_name=device_apis')
			.toPromise()
			.then(this.extractData)
			.then((data: object[]) => plainToClass(AppApi, data))
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
