import { Component, Input } from '@angular/core';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';

import { DevicesService } from './devices.service';

import { WorkingDevice } from '../models/device';
import { DeviceType } from '../models/deviceType';
 
@Component({
	selector: 'device-modal',
	templateUrl: 'client/devices/devices.modal.html',
	styleUrls: [
		'client/devices/devices.css'
	],
	providers: [DevicesService]
})
export class DevicesModalComponent {
	@Input() workingDevice: WorkingDevice = new WorkingDevice();
	@Input() title: string;
	@Input() submitText: string;
	@Input() appNames: string[] = [];
	@Input() deviceTypes: DeviceType[] = [];

	deviceTypesForApp: DeviceType[] = [];
	// save device type fields on saving/loading so we don't clear all progress if we switch device type
	// e.g. { 'router': { 'ip': '127.0.0.1', ... }, ... }
	deviceTypeFields: { [key: string]: {}} = {};
	selectedDeviceType: DeviceType;

	constructor(private devicesService: DevicesService, private activeModal: NgbActiveModal, private toastyService:ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';

		//For an existing device, set our available device types and store the known fields for our device type
		if (this.workingDevice.app) this.deviceTypesForApp = this.deviceTypes.filter(dt => dt.app === this.workingDevice.app);
		if (this.workingDevice.type) this.deviceTypeFields[this.workingDevice.type] = this.workingDevice.fields;
	}

	handleAppSelection(event: any, app: string): void {
		this.workingDevice.app = app;
		this.deviceTypesForApp = this.deviceTypes.filter(dt => dt.app === app);
		if (this.selectedDeviceType && this.selectedDeviceType.app !== app) this._clearDeviceTypeData();
	}

	handleDeviceTypeSelection(event: any, deviceType: string): void {
		//If we just cleared our device type selection, clear our device type data from the working device and any temp storage
		if (!deviceType) {
			this._clearDeviceTypeData();
			return;
		}
		//Grab the first device type that matches our app and newly selected type
		this.selectedDeviceType = this.deviceTypes.filter(dt => dt.app === this.workingDevice.app && dt.name === deviceType)[0];
		//Set the type on our working device
		this.workingDevice.type = deviceType;
		//Set our fields to whatever's stored or a new object
		this.workingDevice.fields = this.deviceTypeFields[deviceType] = this.deviceTypeFields[deviceType] || this._getDefaultValues(this.selectedDeviceType);
	}

	_getDefaultValues(deviceType: DeviceType): { [key: string]: any } {
		let out: { [key: string]: any } = {};

		deviceType.fields.forEach(field => {
			if (field.default) out[field.name] = field.default;
			else out[field.name] = null;
		});

		return out;
	}

	_clearDeviceTypeData(): void {
		this.selectedDeviceType = null;
		this.workingDevice.type = null;
		this.workingDevice.fields = null;
	}

	submit(): void {
		if (!this.validate()) return;
		
		let toSubmit = this.workingDevice.toDevice();

		//If device has an ID, device already exists, call update
		if (this.workingDevice.id) {
			this.devicesService
				.editDevice(toSubmit)
				.then(device => this.activeModal.close({
					device: device,
					isEdit: true
				}))
				.catch(e => this.toastyService.error(e.message));
		}
		else {
			this.devicesService
				.addDevice(toSubmit)
				.then(device => this.activeModal.close({
					device: device,
					isEdit: false
				}))
				.catch(e => this.toastyService.error(e.message));
		}
	}

	validate(): boolean {
		return true;
	}

	getMin(field: any) {
		console.log(field);
		if (!field.minimum === undefined && !field.exclusiveMinimum === undefined) return null;

		if (field.exclusiveMinimum !== undefined) return field.exclusiveMinimum + 1;
		if (field.minimum !== undefined) return field.minimum;
	}

	getMax(field: any) {
		if (!field.maximum === undefined && !field.exclusiveMaximum === undefined) return null;

		if (field.exclusiveMaximum !== undefined) return field.exclusiveMaximum - 1;
		if (field.maximum !== undefined) return field.maximum;
	}
}