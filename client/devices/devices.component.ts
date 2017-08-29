import { Component } from '@angular/core';
import { FormControl } from '@angular/forms';
import * as _ from 'lodash';
import { NgbModal, NgbActiveModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';
import { Select2OptionData } from 'ng2-select2';

import { DevicesModalComponent } from './devices.modal.component';

import { DevicesService } from './devices.service';

import { Device } from '../models/device';
import { DeviceType } from '../models/deviceType';

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
	displayDevices: Device[] = [];
	appNames: string[] = [];
	availableApps: Select2OptionData[] = [];
	appSelectConfig: Select2Options;
	deviceTypes: DeviceType[] = [];
	selectedApps: string[] = [];
	filterQuery: FormControl = new FormControl();

	constructor(private devicesService: DevicesService, private modalService: NgbModal, private toastyService:ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';

		this.appSelectConfig = {
			width: '100%',
			multiple: true,
			allowClear: true,
			placeholder: 'Filter by app(s)...',
			closeOnSelect: false,
		};

		this.getDevices();
		this.getApps();
		this.getDeviceTypes();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterDevices());
	}

	appSelectChange($event: any): void {
		this.selectedApps = $event.value;
		this.filterDevices();
	}

	filterDevices(): void {
		let searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayDevices = this.devices.filter((device) => {
			return (device.name.toLocaleLowerCase().includes(searchFilter) ||
				device.app.toLocaleLowerCase().includes(searchFilter) ||
				device.ip.includes(searchFilter) ||
				device.port.toString().includes(searchFilter)) &&
				(this.selectedApps.length ? this.selectedApps.indexOf(device.app) > -1 : true);
		});
	}

	getDevices(): void {
		this.devicesService
			.getDevices()
			.then(devices => this.displayDevices = this.devices = devices)
			.catch(e => this.toastyService.error(`Error retrieving devices: ${e.message}`));
			
	}

	addDevice(): void {
		const modalRef = this.modalService.open(DevicesModalComponent);
		modalRef.componentInstance.title = 'Add New Device';
		modalRef.componentInstance.submitText = 'Add Device';
		modalRef.componentInstance.appNames = this.appNames;
		modalRef.componentInstance.deviceTypes = this.deviceTypes;

		this._handleModalClose(modalRef);
	}

	editDevice(device: Device): void {
		const modalRef = this.modalService.open(DevicesModalComponent);
		modalRef.componentInstance.title = `Edit Device ${device.name}`;
		modalRef.componentInstance.submitText = 'Save Changes';
		modalRef.componentInstance.appNames = this.appNames;
		modalRef.componentInstance.deviceTypes = this.deviceTypes;

		modalRef.componentInstance.workingDevice = _.cloneDeep(device);

		this._handleModalClose(modalRef);
	}

	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => {
				//Handle modal dismiss
				if (!result || !result.device) return;

				//On edit, find and update the edited item
				if (result.isEdit) {
					let toUpdate = _.find(this.devices, d => d.id === result.device.id);
					Object.assign(toUpdate, result.device);

					this.filterDevices();

					this.toastyService.success(`Device "${result.device.name}" successfully edited.`);
				}
				//On add, push the new item
				else {
					this.devices.push(result.device);

					this.filterDevices();

					this.toastyService.success(`Device "${result.device.name}" successfully added.`);
				}
			},
			(error) => { if (error) this.toastyService.error(error.message); });
	}

	deleteDevice(deviceToDelete: Device): void {
		if (!confirm(`Are you sure you want to delete the device "${deviceToDelete.name}"?`)) return;

		this.devicesService
			.deleteDevice(deviceToDelete.id)
			.then(() => {
				this.devices = _.reject(this.devices, device => device.id === deviceToDelete.id);

				this.filterDevices();

				this.toastyService.success(`Device "${deviceToDelete.name}" successfully deleted.`);
			})
			.catch(e => this.toastyService.error(`Error deleting device: ${e.message}`));
	}

	getApps(): void {
		this.devicesService
			.getApps()
			.then((appNames) => {
				appNames.sort();
				this.appNames = appNames;
				this.availableApps = appNames.map((appName) => { return { id: appName, text: appName } });
			})
			.catch(e => this.toastyService.error(`Error retrieving apps: ${e.message}`));
	}

	getDeviceTypes(): void {
		this.devicesService
			.getDeviceTypes()
			.then(deviceTypes => this.deviceTypes = deviceTypes)
			.catch(e => this.toastyService.error(`Error retrieving device types: ${e.message}`));
	}
}