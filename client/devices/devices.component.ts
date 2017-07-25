import { Component } from '@angular/core';
import * as _ from 'lodash';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

import { DevicesModalComponent } from './devices.modal.component';

import { DevicesService } from './devices.service';

import { Device } from '../models/device';

@Component({
	selector: 'devices-component',
	templateUrl: 'client/devices/devices.html',
	styleUrls: [
		'client/devices/devices.css',
	],
	providers: [DevicesService]
})
export class DevicesComponent {

	//Device Data Table params
	devices: Device[] = [];
	filterQuery: string = "";

	constructor(private devicesService: DevicesService, private modalService: NgbModal) {
		this.getDevices();
	}

	getDevices(): void {
		this.devicesService
			.getDevices()
			.then(devices => this.devices = devices);
	}

	addDevice(): void {
		const modalRef = this.modalService.open(DevicesModalComponent);
		modalRef.componentInstance.title = 'Add New Device';
		modalRef.componentInstance.submitText = 'Add Device';

		modalRef.componentInstance.workingDevice = new Device();
	}

	editDevice(device: Device): void {
		const modalRef = this.modalService.open(DevicesModalComponent);
		modalRef.componentInstance.title = `Edit Device ${device.name}`;
		modalRef.componentInstance.submitText = 'Save Changes';

		modalRef.componentInstance.workingDevice = _.cloneDeep(device);
	}

	deleteDevice(deviceToDelete: Device): void {
		if (!confirm(`Are you sure you want to delete the device "${deviceToDelete.name}"?`)) return;

		this.devicesService
			.deleteDevice(deviceToDelete.id)
			.then(() => this.devices = _.reject(this.devices, device => device.id === deviceToDelete.id))
			.catch(e => console.log(e));
	}
}


// @Component({
//   	selector: 'device-modal',
// 	templateUrl: 'client/devices/devices.device.modal.html',
// 	// styleUrls: [
// 	// 	'client/devices/devices.device.modal.css',
// 	// ],
// 	// providers: [DevicesService]
// })
// export class DeviceModalComponent {
// 	public visible = false;
// 	public visibleAnimate = false;

// 	public show(): void {
// 		this.visible = true;
// 		setTimeout(() => this.visibleAnimate = true, 100);
// 	}

// 	public hide(): void {
// 		this.visibleAnimate = false;
// 		setTimeout(() => this.visible = false, 300);
// 	}

// 	public validate(): void {
		
// 	}

// 	public onContainerClicked(event: MouseEvent): void {
// 		if ((<HTMLElement>event.target).classList.contains('modal')) {
// 		this.hide();
// 		}
// 	}
// }