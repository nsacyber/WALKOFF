import { Component, ViewEncapsulation, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import { Select2OptionData } from 'ng2-select2';

import { DevicesModalComponent } from './devices.modal.component';

import { DevicesService } from './devices.service';

import { Device } from '../models/device';
import { AppApi } from '../models/api/appApi';
import { GenericObject } from '../models/genericObject';

@Component({
	selector: 'devices-component',
	templateUrl: './devices.html',
	styleUrls: [
		'./devices.css',
	],
	encapsulation: ViewEncapsulation.None,
	providers: [DevicesService],
})
export class DevicesComponent implements OnInit {
	//Device Data Table params
	devices: Device[] = [];
	displayDevices: Device[] = [];
	appNames: string[] = [];
	availableApps: Select2OptionData[] = [];
	appSelectConfig: Select2Options;
	appApis: AppApi[] = [];
	selectedApps: string[] = [];
	filterQuery: FormControl = new FormControl();

	constructor(
		private devicesService: DevicesService, private modalService: NgbModal, 
		private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {}

	/**
	 * On component init, initialize the app select2 config, grab devices and device apis from the server.
	 * Set up the search filter to filter devices after 500 ms of inactivity.
	 */
	ngOnInit(): void {
		this.toastyConfig.theme = 'bootstrap';

		this.appSelectConfig = {
			width: '100%',
			multiple: true,
			allowClear: true,
			placeholder: 'Filter by app(s)...',
			closeOnSelect: false,
		};

		this.getDevices();
		this.getDeviceApis();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterDevices());
	}

	/**
	 * Fired when apps are selected in the select2 box. Calls filter devices which filters based on the selected apps.
	 * @param event	JS event from select2 for app selection.
	 */
	appSelectChange(event: any): void {
		this.selectedApps = event.value;
		this.filterDevices();
	}

	/**
	 * Filters devices based on the selected apps select2, and the value of the search filter input box.
	 * If no apps are selected, assume all apps should be returned.
	 */
	filterDevices(): void {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayDevices = this.devices.filter(device => {
			return (device.name.toLocaleLowerCase().includes(searchFilter) ||
				device.app_name.toLocaleLowerCase().includes(searchFilter)) &&
				(this.selectedApps.length ? this.selectedApps.indexOf(device.app_name) > -1 : true);
		});
	}

	/**
	 * Gets an array of devices from the server/DB and sets them for display in our data table.
	 */
	getDevices(): void {
		this.devicesService
			.getDevices()
			.then(devices => this.displayDevices = this.devices = devices)
			.catch(e => this.toastyService.error(`Error retrieving devices: ${e.message}`));
	}

	/**
	 * Spawns a modal for adding a new device. Passes in the app names and apis for usage in the modal.
	 */
	addDevice(): void {
		const modalRef = this.modalService.open(DevicesModalComponent);
		modalRef.componentInstance.title = 'Add New Device';
		modalRef.componentInstance.submitText = 'Add Device';
		modalRef.componentInstance.appNames = this.appNames;
		modalRef.componentInstance.appApis = this.appApis;

		this._handleModalClose(modalRef);
	}

	/**
	 * Spawns a modal for editing an existing device. Passes in the app names and apis for usage in the modal.
	 */
	editDevice(device: Device): void {
		const modalRef = this.modalService.open(DevicesModalComponent);
		modalRef.componentInstance.title = `Edit Device ${device.name}`;
		modalRef.componentInstance.submitText = 'Save Changes';
		modalRef.componentInstance.appNames = this.appNames;
		modalRef.componentInstance.appApis = this.appApis;
		modalRef.componentInstance.workingDevice = device.toWorkingDevice();

		this._handleModalClose(modalRef);
	}

	/**
	 * After user confirmation, will delete a given device from the database.
	 * Removes it from our list of devices to display.
	 * @param deviceToDelete Device to delete
	 */
	deleteDevice(deviceToDelete: Device): void {
		if (!confirm(`Are you sure you want to delete the device "${deviceToDelete.name}"?`)) { return; }

		this.devicesService
			.deleteDevice(deviceToDelete.id)
			.then(() => {
				this.devices = this.devices.filter(device => device.id !== deviceToDelete.id);

				this.filterDevices();

				this.toastyService.success(`Device "${deviceToDelete.name}" successfully deleted.`);
			})
			.catch(e => this.toastyService.error(`Error deleting device: ${e.message}`));
	}

	/**
	 * Gets an array of AppApi objects which only contain their DeviceApis.
	 * AppApis are passed into the add/edit modal to handle custom device fields.
	 * Also builds the available apps data for the app select2.
	 */
	getDeviceApis(): void {
		this.devicesService
			.getDeviceApis()
			.then(appApis => {
				this.appApis = appApis;
				this.appNames = appApis.map(a => a.name);
				this.availableApps = this.appNames.map((appName) => ({ id: appName, text: appName }));
			})
			.catch(e => this.toastyService.error(`Error retrieving device types: ${e.message}`));
	}

	/**
	 * Gets a string representation of the custom fields specified on a device.
	 * Removes quotations for easier reading.
	 * @param device Device to build a custom fields string for
	 */
	getCustomFields(device: Device): string {
		const obj: GenericObject = {};
		device.fields.forEach(element => {
			if (element.value) { obj[element.name] = element.value; }
		});
		let out = JSON.stringify(obj, null, 1);
		out = out.substr(1, out.length - 2).replace(/"/g, '');
		return out;
	}

	/**
	 * On closing an add/edit modal (on clicking save), we will add or update existing devices for display.
	 * @param modalRef ModalRef that is being closed
	 */
	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => {
				//Handle modal dismiss
				if (!result || !result.device) { return; }

				//On edit, find and update the edited item
				if (result.isEdit) {
					const toUpdate = this.devices.find(d => d.id === result.device.id);
					Object.assign(toUpdate, result.device);

					this.filterDevices();

					this.toastyService.success(`Device "${result.device.name}" successfully edited.`);
				} else {
					this.devices.push(result.device);

					this.filterDevices();

					this.toastyService.success(`Device "${result.device.name}" successfully added.`);
				}
			},
			(error) => { if (error) { this.toastyService.error(error.message); } });
	}
}
