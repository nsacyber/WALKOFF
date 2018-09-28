import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { plainToClass } from 'class-transformer';

import { Device } from '../models/device';
import { AppApi } from '../models/api/appApi';
import { UtilitiesService } from '../utilities.service';

@Injectable()
export class DevicesService {
	constructor (private http: HttpClient, private utils: UtilitiesService) {}

	/**
	 * Asynchronously returns an array of all existing devices from the server.
	 */
	getAllDevices(): Promise<Device[]> {
		return this.utils.paginateAll<Device>(this.getDevices.bind(this));
	}

	/**
	 * Asynchronously returns an array of existing devices from the server.
	 */
	getDevices(page: number = 1): Promise<Device[]> {
		return this.http.get(`/api/devices?page=${ page }`)
			.toPromise()
			.then((data) => plainToClass(Device, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asynchronously sends a device to be added to the DB and returns the added device.
	 * @param device Device to add
	 */
	addDevice(device: Device): Promise<Device> {
		return this.http.post('/api/devices', device)
			.toPromise()
			.then((data) => plainToClass(Device, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asynchronously sends a device to be updated within the DB and returns the edited device.
	 * @param device Device to edit
	 */
	editDevice(device: Device): Promise<Device> {
		return this.http.patch('/api/devices', device)
			.toPromise()
			.then((data) => plainToClass(Device, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asyncronously deletes a device from the DB and simply returns success.
	 * @param deviceId Device ID to delete
	 */
	deleteDevice(deviceId: number): Promise<void> {
		return this.http.delete(`/api/devices/${deviceId}`)
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asynchronously returns a list of AppApi objects for all our loaded Apps.
	 * AppApi objects are scoped to only contain device apis.
	 */
	getDeviceApis(): Promise<AppApi[]> {
		return this.http.get('api/apps/apis?field_name=device_apis')
			.toPromise()
			.then((data) => plainToClass(AppApi, data as Object[]))
			// Clear out any apps without device apis
			.then((appApis: AppApi[]) => appApis.filter(a => a.device_apis && a.device_apis.length))
			.catch(this.utils.handleResponseError);
	}
}
