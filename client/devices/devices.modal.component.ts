import { Component, Input } from '@angular/core';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

import { DevicesService } from './devices.service';

import { Device } from '../models/device';
 
@Component({
	selector: 'device-modal',
	templateUrl: 'client/devices/devices.modal.html',
	styleUrls: [
		'client/devices/devices.css'
	]
})
export class DevicesModalComponent {
	@Input() workingDevice: Device;
	@Input() title: string;
	@Input() submitText: string;

	constructor(private devicesService: DevicesService, private activeModal: NgbActiveModal) { }

	submit(): void {
		if (!this.validate()) return;

		//If user has an ID, user already exists, call update
		if (this.workingDevice.id) {
			this.devicesService
				.editDevice(this.workingDevice)
				.then(device => this.activeModal.close(device))
				.catch(e => console.log(e));
		}
		else {
			this.devicesService
				.addDevice(this.workingDevice)
				.then(device => this.activeModal.close(device))
				.catch(e => console.log(e));
		}
	}

	validate(): boolean {
		return true;
	}
}