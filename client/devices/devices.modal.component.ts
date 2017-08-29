import { Component, Input } from '@angular/core';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';

import { DevicesService } from './devices.service';

import { Device } from '../models/device';
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
	@Input() workingDevice: Device = new Device();
	@Input() title: string;
	@Input() submitText: string;
	@Input() appNames: string[] = [];
	@Input() deviceTypes: DeviceType[] = [];

	constructor(private devicesService: DevicesService, private activeModal: NgbActiveModal, private toastyService:ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';
	}

	submit(): void {
		if (!this.validate()) return;

		//If device has an ID, device already exists, call update
		if (this.workingDevice.id) {
			this.devicesService
				.editDevice(this.workingDevice)
				.then(device => this.activeModal.close({
					device: device,
					isEdit: true
				}))
				.catch(e => this.toastyService.error(e.message));
		}
		else {
			this.devicesService
				.addDevice(this.workingDevice)
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
}