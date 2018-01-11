import { Component, ViewEncapsulation, Input } from '@angular/core';
import { Select2OptionData } from 'ng2-select2/ng2-select2';

import { Workflow } from '../models/playbook/workflow';
import { Action } from '../models/playbook/action';
import { ParameterApi } from '../models/api/parameterApi';
import { ParameterSchema } from '../models/api/parameterSchema';
import { Argument } from '../models/playbook/argument';
import { GenericObject } from '../models/genericObject';
import { User } from '../models/user';
import { Role } from '../models/role';

const AVAILABLE_TYPES = ['string', 'number', 'boolean'];

@Component({
	selector: 'playbook-argument-component',
	templateUrl: './playbook.argument.html',
	styleUrls: [],
	encapsulation: ViewEncapsulation.None,
	providers: [],
})
export class PlaybookArgumentComponent {
	@Input() id: number;
	@Input() argument: Argument;
	@Input() parameterApi: ParameterApi;
	@Input() loadedWorkflow: Workflow;
	@Input() users: User[];
	@Input() roles: Role[];

	propertyName: string = '';
	selectedType: string;
	availableTypes: string[] = AVAILABLE_TYPES;
	arrayTypes: string[] = [];
	objectTypes: GenericObject = {};
	// Simple parameter schema reference so I'm not constantly showing parameterApi.schema
	parameterSchema: ParameterSchema;
	selectData: Select2OptionData[];
	selectConfig: Select2Options;
	selectInitialValue: number[];

	// tslint:disable-next-line:no-empty
	constructor() { }

	ngOnInit(): void {
		this.parameterSchema = this.parameterApi.schema;
		if (this.argument.reference == null) { this.argument.reference = ''; }
		if (this.argument.value == null) {
			if (this.parameterSchema.type === 'array') { 
				this.argument.value = [];
			} else if (this.parameterSchema.type === 'object') {
				this.argument.value = {};
			}
		} else if (this.parameterSchema.type === 'array') {
			for (const item of (this.argument.value as any[])) {
				this.arrayTypes.push(typeof(item));
			}
		} else if (this.parameterSchema.type === 'object') {
			for (const key in (this.argument.value as GenericObject)) {
				if ((this.argument.value as GenericObject).hasOwnProperty(key)) {
					this.objectTypes[key] = typeof((this.argument.value as GenericObject)[key]);
				}
			}
		}
		this.selectedType = this.availableTypes[0];

		if (this.isUserSelect(this.parameterSchema)) {
			this.selectData = this.users.map(user => {
				return { id: user.id.toString(), text: user.username };
			});

			this.selectConfig = {
				width: '100%',
				placeholder: 'Select user',
			};

			if (this.parameterSchema.type === 'array') {
				this.selectConfig.placeholder += '(s)';
				this.selectConfig.multiple = true;
				this.selectConfig.allowClear = true;
				this.selectConfig.closeOnSelect = false;
			}

			this.selectInitialValue = JSON.parse(JSON.stringify(this.argument.value));
		}
		if (this.isRoleSelect(this.parameterSchema)) {
			this.selectData = this.roles.map(role => {
				return { id: role.id.toString(), text: role.name };
			});

			this.selectConfig = {
				width: '100%',
				placeholder: 'Select role',
			};

			if (this.parameterSchema.type === 'array') {
				this.selectConfig.placeholder += '(s)';
				this.selectConfig.multiple = true;
				this.selectConfig.allowClear = true;
				this.selectConfig.closeOnSelect = false;
			}

			this.selectInitialValue = JSON.parse(JSON.stringify(this.argument.value));
		}

	}

	/**
	 * Event fired on the select2 change for users/roles. Updates the value based on the event value.
	 * @param $event JS Event Fired
	 */
	selectChange($event: any): void {
		// Convert strings to numbers here
		if (this.parameterSchema.type === 'array') {
			const array = $event.value.map((id: string) => +id);
			this.argument.value = array;
		} else {
			this.argument.value = +$event.value;
		}
	}

	addItem(): void {
		switch (this.selectedType) {
			case 'string':
				(this.argument.value as any[]).push('');
				break;
			case 'number':
				(this.argument.value as any[]).push(null);
				break;
			case 'boolean':
				(this.argument.value as any[]).push(false);
				break;
			default:
				return;
		}
		this.arrayTypes.push(this.selectedType);
	}

	moveUp(index: number): void {
		const idAbove = index - 1;
		const toBeSwapped = (this.argument.value as any[])[idAbove];
		const arrayTypeToBeSwapped = this.arrayTypes[idAbove];

		(this.argument.value as any[])[idAbove] = (this.argument.value as any[])[index];
		(this.argument.value as any[])[index] = toBeSwapped;

		this.arrayTypes[idAbove] = this.arrayTypes[index];
		this.arrayTypes[index] = arrayTypeToBeSwapped;
	}

	moveDown(index: number): void {
		const idBelow = index + 1;
		const toBeSwapped = (this.argument.value as any[])[idBelow];
		const arrayTypeToBeSwapped = this.arrayTypes[idBelow];

		(this.argument.value as any[])[idBelow] = (this.argument.value as any[])[index];
		(this.argument.value as any[])[index] = toBeSwapped;

		this.arrayTypes[idBelow] = this.arrayTypes[index];
		this.arrayTypes[index] = arrayTypeToBeSwapped;
	}

	removeItem(index: number): void {
		(this.argument.value as any[]).splice(index, 1);
		this.arrayTypes.splice(index, 1);
	}

	addProperty(): void {
		if ((this.argument.value as object).hasOwnProperty(this.propertyName)) { return; }
		this.propertyName = this.propertyName.trim();
		switch (this.selectedType) {
			case 'string':
				(this.argument.value as any)[this.propertyName] = '';
				break;
			case 'number':
				(this.argument.value as any)[this.propertyName] = null;
				break;
			case 'boolean':
				(this.argument.value as any)[this.propertyName] = false;
				break;
			default:
				return;
		}
		this.objectTypes[this.propertyName] = this.selectedType;
		this.propertyName = '';
	}

	removeProperty(key: string): void {
		delete (this.argument.value as any)[key];
		delete this.objectTypes[key];
	}

	trackArraysBy(index: any, item: any) {
		return index;
	}

	// TODO: maybe somehow recursively find actions that may occur before. Right now it just returns all of them.
	getPreviousActions(): Action[] {
		return this.loadedWorkflow.actions;
	}

	/**
	 * Gets the minimum value to check against for JSON Schema minimum / exclusiveMinimum parameters
	 * @param schema JSON Schema object
	 */
	getMin(schema: ParameterSchema): number {
		if (schema.minimum === undefined) { return null; }
		if (schema.exclusiveMinimum) { return schema.minimum + 1; }
		return schema.minimum;
	}

	/**
	 * Gets the maximum value to check against for JSON Schema maximum / exclusiveMaximum parameters
	 * @param schema JSON Schema Object
	 */
	getMax(schema: ParameterSchema): number {
		if (schema.maximum === undefined) { return null; }
		if (schema.exclusiveMaximum) { return schema.maximum - 1; }
		return schema.maximum;
	}

	/**
	 * Checks if this array is an array of primitives only.
	 * Returns false if the schema is not an array or if it contains user/role types.
	 * @param schema JSON Schema Object to check against
	 */
	isNormalArray(schema: ParameterSchema): boolean {
		if (schema.type !== 'array') { return false; }
		//Is Array Empty?
		if(typeof schema.items !== 'undefined' && schema.items.length > 0){
            if (Array.isArray(schema.items)) {
                    (schema.items as GenericObject[]).forEach(i => {
                        if (i.type === 'user' || i.type === 'role') { return false; }
                    });
		    } else if (schema.items.type === 'user' || schema.items.type === 'role') { return false; }
		}
		return true;
	}

	/**
	 * Checks if this schema represents a user select (single or multiple via array type).
	 * @param schema JSON Schema Object to check against
	 */
	isUserSelect(schema: ParameterSchema): boolean {
		if (schema.type === 'user' || 
		(schema.type === 'array' && schema.items && !Array.isArray(schema.items) && schema.items.type === 'user')) { 
			return true;
		}

		return false;
	}

	/**
	 * Checks if this schema represents a role select (single or multiple via array type).
	 * @param schema JSON Schema Object to check against
	 */
	isRoleSelect(schema: ParameterSchema): boolean {
		if (schema.type === 'role' || 
		(schema.type === 'array' && schema.items && !Array.isArray(schema.items) && schema.items.type === 'role')) { 
			return true;
		}

		return false;
	}
}
