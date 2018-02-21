import { Component, Input, ChangeDetectorRef, ViewChild, ElementRef, OnInit, AfterViewInit } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';

import { DevicesService } from './devices.service';

import { WorkingDevice } from '../models/workingDevice';
import { AppApi } from '../models/api/appApi';
import { DeviceApi } from '../models/api/deviceApi';
import { ParameterSchema } from '../models/api/parameterSchema';
import { GenericObject } from '../models/genericObject';

@Component({
	selector: 'device-modal',
	templateUrl: './devices.modal.html',
	styleUrls: [
		'./devices.css',
	],
	providers: [DevicesService],
})
export class DevicesModalComponent implements OnInit, AfterViewInit {
	@Input() workingDevice: WorkingDevice = new WorkingDevice();
	@Input() title: string;
	@Input() submitText: string;
	@Input() appNames: string[] = [];
	@Input() appApis: AppApi[] = [];
	@ViewChild('typeRef') typeRef: ElementRef;
	// @ViewChild('deviceForm') form: FormGroup

	deviceTypesForApp: DeviceApi[] = [];
	// save device type fields on saving/loading so we don't clear all progress if we switch device type
	// e.g. { 'router': { 'ip': '127.0.0.1', ... }, ... }
	deviceTypeFields: { [key: string]: {} } = {};
	selectedDeviceType: DeviceApi;
	validationErrors: { [key: string]: string } = {};
	encryptedConfirmFields: { [key: string]: string } = {};
	encryptedFieldsToBeCleared: { [key: string]: boolean } = {};

	constructor (
		private devicesService: DevicesService, private activeModal: NgbActiveModal, 
		private toastyService: ToastyService, private toastyConfig: ToastyConfig, private cdr: ChangeDetectorRef,
	) {}

	ngOnInit(): void {
		this.toastyConfig.theme = 'bootstrap';
	}

	ngAfterViewInit(): void {
		//For an existing device, set our available device types and store the known fields for our device type
		if (this.workingDevice.app_name) {
			this.deviceTypesForApp = this.appApis.find(app => app.name === this.workingDevice.app_name).device_apis;
		}
		//Detect changes beforehand so the select box is updated
		this.cdr.detectChanges();
		if (this.workingDevice.type) {
			this.deviceTypeFields[this.workingDevice.type] = this.workingDevice.fields;
			this.typeRef.nativeElement.value = this.workingDevice.type;
			this.handleDeviceTypeSelection(null, this.workingDevice.type);
		}
		//Detect changes once more to actually use the selected device type
		this.cdr.detectChanges();
	}

	/**
	 * On selecting an app in the app select, get the DeviceTypes for the app from our App Apis.
	 * Also clear device type data if needed.
	 * @param event JS event fired from app select
	 * @param appName App name from the selection
	 */
	handleAppSelection(event: any, appName: string): void {
		this.workingDevice.app_name = appName;
		this.deviceTypesForApp = this.appApis.find(a => a.name === appName).device_apis;
		if (this.selectedDeviceType) { this._clearDeviceTypeData(); }
	}

	/**
	 * On selecting a device type in the device type select, grab the DeviceApi from our AppApis.
	 * Get the default or existing values for our device based on the Device Api.
	 * @param event JS event fired from device type select
	 * @param deviceType Device type from the selection
	 */
	handleDeviceTypeSelection(event: any, deviceType: string): void {
		// If we just cleared our device type selection,
		// clear our device type data from the working device and any temp storage
		if (!deviceType) {
			this._clearDeviceTypeData();
			return;
		}
		// Grab the first device type that matches our app and newly selected type
		this.selectedDeviceType = this.appApis.find(a => a.name === this.workingDevice.app_name)
			.device_apis.find(d => d.name === deviceType);
		// Set the type on our working device
		this.workingDevice.type = deviceType;
		// Set our fields to whatever's stored or a new object
		this.workingDevice.fields = 
			this.deviceTypeFields[deviceType] = 
			this.deviceTypeFields[deviceType] || this._getDefaultValues(this.selectedDeviceType);

		this._getEncryptedConfirmFields(this.selectedDeviceType);
		this.validationErrors = {};
	}

	/**
	 * On checking/unchecking an encrypted field clear box, we are marking if it is to be cleared on save.
	 * This is needed because we need a distinction between passing empty string and null.
	 * @param fieldName Name of field to toggle
	 * @param isChecked Determine if we're clearing this field on save.
	 */
	handleEncryptedFieldClear(fieldName: string, isChecked: boolean): void {
		this.encryptedFieldsToBeCleared[fieldName] = isChecked;
	}

	/**
	 * Submits the add/edit device modal.
	 * If we're editing a device, we also want to handle removing
	 * encrypted fields by setting them as '' rather than just passing null.
	 * Calls POST/PUT based upon add/edit and returns the added/updated device from the server.
	 */
	submit(): void {
		if (!this.validate()) { return; }

		const toSubmit = WorkingDevice.toDevice(this.workingDevice);

		//If device has an ID, device already exists, call update
		if (this.workingDevice.id) {
			const self = this;
			toSubmit.fields.forEach((field, index, array) => {
				const ftype = self.selectedDeviceType.fields.find(ft => ft.name === field.name);
	
				if (!ftype.encrypted) { return; }
	
				//If we are to be clearing our value, please set it to empty string and return
				if (self.encryptedFieldsToBeCleared[field.name]) { 
					field.value = '';
				} else if ((typeof(field.value) === 'string' && !field.value.trim()) ||
					(typeof(field.value) === 'number' && !field.value)) { array.splice(index, 1); }
			});

			this.devicesService
				.editDevice(toSubmit)
				.then(device => this.activeModal.close({
					device,
					isEdit: true,
				}))
				.catch(e => this.toastyService.error(e.message));
		} else {
			this.devicesService
				.addDevice(toSubmit)
				.then(device => this.activeModal.close({
					device,
					isEdit: false,
				}))
				.catch(e => this.toastyService.error(e.message));
		}
	}

	/**
	 * Checks if basic info on the top level device params is valid (specified).
	 */
	isBasicInfoValid(): boolean {
		if (this.workingDevice.name && this.workingDevice.name.trim() && 
			this.workingDevice.app_name && this.workingDevice.type) { return true; }

		return false;
	}

	/**
	 * Performs validation on each Device field based on the matching ParameterSchema for the DeviceApi.
	 */
	validate(): boolean {
		const self = this;
		this.validationErrors = {};
		const inputs = this.workingDevice.fields;

		//Trim whitespace out of our inputs first
		Object.keys(inputs).forEach(function (key) {
			if (typeof(inputs[key]) === 'string') {
				inputs[key] = (inputs[key] as string).trim();
				//Also trim encrypted confirm fields if necessary
				if (self.encryptedConfirmFields[key]) { 
					self.encryptedConfirmFields[key] = self.encryptedConfirmFields[key].trim();
				}
			}
		});

		this.selectedDeviceType.fields.forEach(field => {
			if (field.required) {
				if (inputs[field.name] == null ||
					(typeof inputs[field.name] === 'string' && !inputs[field.name]) ||
					(typeof inputs[field.name] === 'number' && inputs[field.name] === null)) {
					this.validationErrors[field.name] = `You must enter a value for ${field.name}.`;
					return;
				}
			}
			switch (field.schema.type) {
				//For strings, check against min/max length, regex pattern, or enum constraints
				case 'string':
					if (inputs[field.name] == null) { inputs[field.name] = ''; }

					if (field.encrypted && 
						!this.encryptedFieldsToBeCleared[field.name] && 
						this.encryptedConfirmFields[field.name] !== inputs[field.name]) {
						this._concatValidationMessage(field.name, `The values for ${field.name} do not match.`);
					}
					if (field.schema.enum) {
						const enumArray: string[] = field.schema.enum.slice(0);
						if (!field.required) { enumArray.push(''); }
						if (enumArray.indexOf(inputs[field.name]) < 0) {
							this._concatValidationMessage(field.name, 'You must select a value from the list.');
						}
					}

					//We're past the required check; Don't do any more validation if we have an empty string as input
					if (!inputs[field.name]) { break; }

					if (field.schema.minLength !== undefined && inputs[field.name].length < field.schema.minLength) {
						this._concatValidationMessage(field.name, `Must be at least ${field.schema.minLength} characters.`);
					}
					if (field.schema.maxLength !== undefined && inputs[field.name].length > field.schema.maxLength) {
						this._concatValidationMessage(field.name, `Must be at most ${field.schema.minLength} characters.`);
					}
					if (field.schema.pattern && !new RegExp(field.schema.pattern as string).test(inputs[field.name])) {
						this._concatValidationMessage(field.name, `Input must match a given pattern: ${field.schema.pattern}.`);
					}
					break;
				//For numbers, check against min/max and multipleOf constraints
				case 'number':
				case 'integer':
					//We're past the required check; if number is null, don't do any more validation
					if (inputs[field.name] == null) { break; }

					const min = this.getMin(field.schema);
					const max = this.getMax(field.schema);
					if (min !== null && inputs[field.name] < min) {
						this._concatValidationMessage(field.name, `The minimum value is ${min}.`);
					}
					if (max !== null && inputs[field.name] > max) {
						this._concatValidationMessage(field.name, `The maximum value is ${max}.`);
					}
					if (field.schema.multipleOf !== undefined && inputs[field.name] % field.schema.multipleOf) {
						this._concatValidationMessage(field.name, `The value must be a multiple of ${field.schema.multipleOf}.`);
					}
					break;
				//For booleans, just initialize the value to false if it doesn't exist
				case 'boolean':
					inputs[field.name] = inputs[field.name] || false;
					break;
				default:
					this._concatValidationMessage(field.name, `The type specified for field ${field.name} is invalid.`);
					break;
			}
		});

		if (Object.keys(this.validationErrors).length) { return false; }

		return true;
	}

	/**
	 * Returns the minimum value based on a ParameterSchema's minimum and exclusiveMinimum fields.
	 * @param schema ParameterSchema to check against
	 */
	getMin(schema: ParameterSchema) {
		if (schema.minimum === undefined) { return null; }
		if (schema.exclusiveMinimum) { return schema.minimum + 1; }
		return schema.minimum;
	}

	/**
	 * Returns the maximum value based on a ParameterSchema's maximum and exclusiveMaximum fields.
	 * @param schema ParameterSchema to check against
	 */
	getMax(schema: ParameterSchema) {
		if (schema.maximum === undefined) { return null; }
		if (schema.exclusiveMaximum) { return schema.maximum - 1; }
		return schema.maximum;
	}

	/**
	 * Sets a component variable to track confirm fields for encrypted values.
	 * This is so we can allow the form to have encrypted values entered twice such that a user doesn't fat finger it.
	 * @param deviceType DeviceApi to check for encrypted fields.
	 */
	private _getEncryptedConfirmFields(deviceType: DeviceApi): void {
		this.encryptedConfirmFields = {};
		deviceType.fields.forEach(field => {
			if (field.encrypted) { this.encryptedConfirmFields[field.name] = ''; }
		});
	}

	/**
	 * Returns a field with the default value specified if possible.
	 * @param deviceApi Device Api to check against
	 */
	private _getDefaultValues(deviceApi: DeviceApi): GenericObject {
		const out: GenericObject = {};

		deviceApi.fields.forEach(field => {
			if (field.schema.default) {
				out[field.name] = field.schema.default;
			} else {
				out[field.name] = null;
			}
		});

		return out;
	}

	/**
	 * Clears all of our device type data. Used if we switch device types or selected app.
	 */
	private _clearDeviceTypeData(): void {
		this.selectedDeviceType = null;
		this.workingDevice.type = null;
		this.workingDevice.fields = null;
		this.validationErrors = {};
		this.encryptedConfirmFields = {};
	}

	/**
	 * For a given field key in our validationErrors object, add message to the end of the existing message.
	 * @param field Field name to concat validation messages for
	 * @param message Message to concat
	 */
	private _concatValidationMessage(field: string, message: string) {
		if (this.validationErrors[field]) { 
			this.validationErrors[field] += '\n' + message;
		} else { 
			this.validationErrors[field] = message;
		}
	}
}
