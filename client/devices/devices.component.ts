import { Component } from '@angular/core';
// import _ from 'lodash';

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
	devices: Device[];
	filterQuery: string = "";
	rowsOnPage: number = 10;
	sortBy: string = "name";
	sortOrder: string = "asc";
	page: number = 1;

	constructor(private devicesService: DevicesService) {
		this.getDevices();
	}

	getDevices(): void {
		this.devicesService
			.getDevicesForApp('test')
			.then(devices => this.devices = devices);
	}

	addDevice(): void {
		//Open up device add/edit modal
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