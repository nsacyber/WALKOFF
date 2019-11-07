import { Component, Input, ChangeDetectorRef, ViewChild, ElementRef, OnInit, AfterViewInit } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';

import { GlobalsService } from './globals.service';
import { UtilitiesService } from '../utilities.service';

import { WorkingGlobal } from '../models/workingGlobal';
import { AppApi } from '../models/api/appApi';
import { DeviceApi } from '../models/api/deviceApi';
import { ParameterSchema } from '../models/api/parameterSchema';
import { GenericObject } from '../models/genericObject';

@Component({
	selector: 'global-modal',
	templateUrl: './globals.modal.html',
	styleUrls: [
		'./globals.scss',
	],
	providers: [GlobalsService, UtilitiesService],
})
export class GlobalsModalComponent implements OnInit, AfterViewInit {
	@Input() workingGlobal: WorkingGlobal = new WorkingGlobal();
	@Input() title: string;
	@Input() submitText: string;
	@Input() appNames: string[] = [];
	@Input() appApis: AppApi[] = [];
	@ViewChild('typeRef', { static: true }) typeRef: ElementRef;
	// @ViewChild('globalForm') form: FormGroup

	globalTypesForApp: DeviceApi[] = [];
	// save global type fields on saving/loading so we don't clear all progress if we switch global type
	// e.g. { 'router': { 'ip': '127.0.0.1', ... }, ... }
	globalTypeFields: { [key: string]: {} } = {};
	selectedGlobalType: DeviceApi;
	validationErrors: { [key: string]: string } = {};
	encryptedConfirmFields: { [key: string]: string } = {};
	encryptedFieldsToBeCleared: { [key: string]: boolean } = {};

	constructor (
		private globalsService: GlobalsService, public activeModal: NgbActiveModal, 
		private toastrService: ToastrService, private cdr: ChangeDetectorRef,
	) {}

	ngOnInit(): void {
	}

	ngAfterViewInit(): void {
		//For an existing global, set our available global types and store the known fields for our global type
		if (this.workingGlobal.app_name) {
			this.globalTypesForApp = this.appApis.find(app => app.name === this.workingGlobal.app_name).device_apis;
		}
		//Detect changes beforehand so the select box is updated
		this.cdr.detectChanges();
		if (this.workingGlobal.type) {
			this.globalTypeFields[this.workingGlobal.type] = this.workingGlobal.fields;
			this.typeRef.nativeElement.value = this.workingGlobal.type;
			this.handleGlobalTypeSelection(null, this.workingGlobal.type);
		}
		//Detect changes once more to actually use the selected global type
		this.cdr.detectChanges();
	}

	/**
	 * On selecting an app in the app select, get the GlobalTypes for the app from our App Apis.
	 * Also clear global type data if needed.
	 * @param event JS event fired from app select
	 * @param appName App name from the selection
	 */
	handleAppSelection(event: any, appName: string): void {
		this.workingGlobal.app_name = appName;
		this.globalTypesForApp = this.appApis.find(a => a.name === appName).device_apis;
		if (this.selectedGlobalType) { this._clearGlobalTypeData(); }
	}

	/**
	 * On selecting a global type in the global type select, grab the DeviceApi from our AppApis.
	 * Get the default or existing values for our global based on the Global Api.
	 * @param event JS event fired from global type select
	 * @param globalType Global type from the selection
	 */
	handleGlobalTypeSelection(event: any, globalType: string): void {
		// If we just cleared our global type selection,
		// clear our global type data from the working global and any temp storage
		if (!globalType) {
			this._clearGlobalTypeData();
			return;
		}
		// Grab the first global type that matches our app and newly selected type
		this.selectedGlobalType = this.appApis.find(a => a.name === this.workingGlobal.app_name)
			.device_apis.find(d => d.name === globalType);
		// Set the type on our working global
		this.workingGlobal.type = globalType;
		// Set our fields to whatever's stored or a new object
		this.workingGlobal.fields = 
			this.globalTypeFields[globalType] = 
			this.globalTypeFields[globalType] || this._getDefaultValues(this.selectedGlobalType);

		this._getEncryptedConfirmFields(this.selectedGlobalType);
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
	 * Submits the add/edit global modal.
	 * If we're editing a global, we also want to handle removing
	 * encrypted fields by setting them as '' rather than just passing null.
	 * Calls POST/PUT based upon add/edit and returns the added/updated global from the server.
	 */
	submit(): void {
		if (!this.validate()) { return; }

		// const toSubmit = WorkingGlobal.toGlobal(this.workingGlobal);

		// //If global has an ID, global already exists, call update
		// if (this.workingGlobal.id) {
		// 	toSubmit.fields.forEach((field, index, array) => {
		// 		const ftype = this.selectedGlobalType.fields.find(ft => ft.name === field.name);
	
		// 		if (!ftype.encrypted) { return; }
	
		// 		//If we are to be clearing our value, please set it to empty string and return
		// 		if (this.encryptedFieldsToBeCleared[field.name]) { 
		// 			field.value = '';
		// 		} else if ((typeof(field.value) === 'string' && !field.value.trim()) ||
		// 			(typeof(field.value) === 'number' && !field.value)) { array.splice(index, 1); }
		// 	});

		// 	this.globalsService
		// 		.editGlobal(toSubmit)
		// 		.then(global => this.activeModal.close({
		// 			global,
		// 			isEdit: true,
		// 		}))
		// 		.catch(e => this.toastrService.error(e.message));
		// } else {
		// 	this.globalsService
		// 		.addGlobal(toSubmit)
		// 		.then(global => this.activeModal.close({
		// 			global,
		// 			isEdit: false,
		// 		}))
		// 		.catch(e => this.toastrService.error(e.message));
		// }
	}

	/**
	 * Checks if basic info on the top level global params is valid (specified).
	 */
	isBasicInfoValid(): boolean {
		if (this.workingGlobal.name && this.workingGlobal.name.trim() && 
			this.workingGlobal.app_name && this.workingGlobal.type) { return true; }

		return false;
	}

	/**
	 * Performs validation on each Global field based on the matching ParameterSchema for the DeviceApi.
	 */
	validate(): boolean {
		this.validationErrors = {};
		const inputs = this.workingGlobal.fields;

		//Trim whitespace out of our inputs first
		Object.keys(inputs).forEach(key => {
			if (typeof(inputs[key]) === 'string') {
				inputs[key] = (inputs[key] as string).trim();
				//Also trim encrypted confirm fields if necessary
				if (this.encryptedConfirmFields[key]) { 
					this.encryptedConfirmFields[key] = this.encryptedConfirmFields[key].trim();
				}
			}
		});

		this.selectedGlobalType.fields.forEach(field => {
			// if we have a required field, and this field is NOT an edit to an encrypted field,
			// check if we have a value specified
			if (field.required && !(this.workingGlobal.id && field.encrypted)) {
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
	 * @param globalType DeviceApi to check for encrypted fields.
	 */
	private _getEncryptedConfirmFields(globalType: DeviceApi): void {
		this.encryptedConfirmFields = {};
		globalType.fields.forEach(field => {
			if (field.encrypted) { this.encryptedConfirmFields[field.name] = ''; }
		});
	}

	/**
	 * Returns a field with the default value specified if possible.
	 * @param deviceApi Global Api to check against
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
	 * Clears all of our global type data. Used if we switch global types or selected app.
	 */
	private _clearGlobalTypeData(): void {
		this.selectedGlobalType = null;
		this.workingGlobal.type = null;
		this.workingGlobal.fields = null;
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
