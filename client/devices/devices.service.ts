import { Injectable } from '@angular/core';
import { Http, Response, Headers } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Device } from '../models/device';
import { DeviceType } from '../models/deviceType';

@Injectable()
export class DevicesService {
	constructor (private authHttp: JwtHttp) {
	}

	getDevicesForApp(appName: string) : Promise<Device[]> {
		return this.authHttp.get(`/api/apps/${appName}`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device[])
			.catch(this.handleError);
	}

	getAppDevice(appName: string, deviceName: string) : Promise<Device> {
		return this.authHttp.get(`/api/apps/${appName}/devices/${deviceName}`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device)
			.catch(this.handleError);
	}

	getDevices() : Promise<Device[]> {
		return this.authHttp.get(`/api/devices`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device[])
			.catch(this.handleError);
	}

	addDevice(device: Device) : Promise<Device> {
		return this.authHttp.put(`/api/devices`, device)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device)
			.catch(this.handleError);
	}

	editDevice(device: Device) : Promise<Device> {
		return this.authHttp.post(`/api/devices`, device)
			.toPromise()
			.then(this.extractData)
			.then(data => data as Device)
			.catch(this.handleError);
	}

	deleteDevice(deviceId: number) : Promise<void> {
		return this.authHttp.delete(`/api/devices/${deviceId}`)
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	//Only get apps that have device types for the purposes of devices
	getApps() : Promise<string[]> {
		return this.authHttp.get(`/api/apps?has_device_types=true`)
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	getDeviceTypes() : Promise<DeviceType[]> {
		// return Promise.resolve(<DeviceType[]>[
		// 	{
		// 		name: 'Test Device Type',
		// 		app: 'HelloWorld',
		// 		fields: [
		// 			{
		// 				name: 'Text field',
		// 				type: 'string',
		// 				minLength: 5,
		// 				maxLength: 20,
		// 				required: true,
		// 				placeholder: 'enter something please'
		// 			},
		// 			{
		// 				name: 'Encrypted field',
		// 				type: 'string',
		// 				encrypted: true,
		// 				placeholder: 'shh its a secret'
		// 			},
		// 			{
		// 				name: 'Number field',
		// 				type: 'integer',
		// 				minimum: 0,
		// 				exclusiveMaximum: 25,
		// 				multipleOf: 5,
		// 				placeholder: 'this ones a number',
		// 				required: true,
		// 			},
		// 			{
		// 				name: 'Enum field',
		// 				type: 'string',
		// 				enum: ['val 1', 'val 2', 'val 3', 'another val'],
		// 				required: true,
		// 				placeholder: 'this ones a dropdown'
		// 			},
		// 			{
		// 				name: 'Boolean field',
		// 				type: 'boolean'
		// 			}
		// 		]
		// 	},
		// 	{
		// 		name: 'Test Type 2',
		// 		app: 'HelloWorld',
		// 		fields: [
		// 			{
		// 				name: 'Text field',
		// 				type: 'string',
		// 				minLength: 5,
		// 				maxLength: 100,
		// 				pattern: `^([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])\\.([01]?\\d\\d?|2[0-4]\\d|25[0-5])$`
		// 			},
		// 			{
		// 				name: 'Enum field',
		// 				type: 'string',
		// 				enum: ['val 1', 'val 2', 'val 3', 'another val']
		// 			},
		// 			{
		// 				name: 'Encrypted field',
		// 				type: 'string',
		// 				encrypted: true
		// 			},
		// 			{
		// 				name: 'Number field',
		// 				type: 'number',
		// 				default: 10
		// 			},
		// 		]
		// 	}
		// ]);
		return this.authHttp.get(`api/devicetypes`)
			.toPromise()
			.then(this.extractData)
			.then(data => data as DeviceType[])
			.catch(this.handleError);
	}
	
	private extractData (res: Response) {
		let body = res.json();
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
