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

	constructor(private devicesService: DevicesService, private activeModal: NgbActiveModal, private toastyService:ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';
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
}