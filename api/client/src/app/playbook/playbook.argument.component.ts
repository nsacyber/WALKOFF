import { Component, ViewEncapsulation, Input, Output, EventEmitter, OnChanges, ElementRef, ViewChild } from '@angular/core';
import { Select2OptionData } from 'ng2-select2/ng2-select2';

import { Workflow } from '../models/playbook/workflow';
import { Action } from '../models/playbook/action';
import { ParameterApi } from '../models/api/parameterApi';
import { ParameterSchema } from '../models/api/parameterSchema';
import { Argument, Variant } from '../models/playbook/argument';
import { GenericObject } from '../models/genericObject';
import { User } from '../models/user';
import { Role } from '../models/role';
import { Global } from '../models/global';
import { WorkflowNode } from '../models/playbook/WorkflowNode';
import { JsonEditorComponent } from 'ang-jsoneditor';

const AVAILABLE_TYPES = ['string', 'number', 'boolean'];

@Component({
	selector: 'playbook-argument-component',
	templateUrl: './playbook.argument.html',
	styleUrls: [],
	encapsulation: ViewEncapsulation.None,
	providers: [],
})
export class PlaybookArgumentComponent implements OnChanges {
	@Input() id: number;
	@Input() argument: Argument;
	@Input() parameterApi: ParameterApi;
	@Input() selectedAction: Action;
	@Input() loadedWorkflow: Workflow;
	@Input() users: User[];
	@Input() roles: Role[];
	@Input() globals: Global[];
	@Input() branchCounters: any[];

	@ViewChild('jsonEditor', { static: false }) jsonEditor: JsonEditorComponent;

	@Output() createVariable = new EventEmitter<Argument>();

	valueType: string = Variant.STATIC_VALUE;
	valueTypes: any[];

	propertyName: string = '';
	selectedType: string;
	availableTypes: string[] = AVAILABLE_TYPES;
	arrayTypes: string[] = [];
	objectTypes: GenericObject = {};

	// Simple parameter schema reference so I'm not constantly showing parameterApi.schema
	parameterSchema: ParameterSchema;
	selectData: Select2OptionData[];
	selectConfig: Select2Options;
	selectInitialValue: string[];

	initialValue;

	editorOptionsData: any = {
		mode: 'code',
		modes: ['code', 'tree'],
		history: false,
		search: false,
		// mainMenuBar: false,
		navigationBar: false,
		statusBar: false,
		enableSort: false,
		enableTransform: false,
	}
	

	// tslint:disable-next-line:no-empty
	constructor() { }

	/**
	 * On init, we want to ensure our data is correctly formatted.
	 * If reference is null, set it to empty string for editing.
	 * If our value is of type array or object and is null, initalize them as such.
	 * Additionally, if we're array or object types, track the types of the values that currently exist.
	 * Initialize user and role selects if necessary (if schema type user or role is used).
	 */
	ngOnChanges(): void {
		this.initParameterSchema();
		this.initTypeSelector();
		this.initUserSelect();
		this.initRoleSelect();
	}

	initParameterSchema(): void {
		this.parameterSchema = this.parameterApi.json_schema;
		if (this.argument.value == null) {
			if (this.parameterSchema.type === 'array') { 
				this.argument.value = [];
			} else if (this.parameterSchema.type === 'object') {
				this.argument.value = {};
			} else if (this.parameterSchema.type === 'boolean') {
				this.argument.value = false;
			}
		} else if (this.argument.value && this.parameterSchema.type === 'array') {
			for (const item of (this.argument.value as any[])) {
				this.arrayTypes.push(typeof(item));
			}
		} else if (this.argument.value && this.parameterSchema.type === 'object') {
			for (const key in (this.argument.value as GenericObject)) {
				if ((this.argument.value as GenericObject).hasOwnProperty(key)) {
					this.objectTypes[key] = typeof((this.argument.value as GenericObject)[key]);
				}
			}
		}

		// Store initial value for use in JSONeditor widget
		this.initialValue = this.argument.value;
		if (this.parameterSchema) this.editorOptionsData.schema = this.parameterSchema;
	}

	initTypeSelector(): void {
		this.valueTypes = [
			{ id: Variant.STATIC_VALUE, name: 'Static Value'},
			{ id: Variant.ACTION_RESULT, name: 'Action Output'},
			{ id: Variant.WORKFLOW_VARIABLE, name: 'Local'},
			{ id: Variant.GLOBAL, name: 'Global'}
		];

		if (this.argument.variant) this.valueType = this.argument.variant;
		this.selectedType = this.availableTypes[0];
	}

	/**
	 * Initializes the user select2 box for arguments that have { type: 'user' } ParameterSchemas.
	 */
	initUserSelect(): void {
		if (!this.isUserSelect) { return; }

		this.selectData = this.users.map((user) => {
			return { id: user.id.toString(), text: user.username };
		});

		this.selectConfig = {
			width: '100%',
			placeholder: 'Select user',
		};

		this.selectInitialValue = JSON.parse(JSON.stringify(this.argument.value));

		if (this.parameterSchema.type === 'array') {
			this.selectConfig.placeholder += '(s)';
			this.selectConfig.multiple = true;
			this.selectConfig.allowClear = true;
			this.selectConfig.closeOnSelect = false;
			if (Array.isArray(this.argument.value)) 
				this.selectInitialValue = this.argument.value.map((val: number) => val.toString());
		}
	}

	/**
	 * Initializes the role select2 box for arguments that have { type: 'role' } ParameterSchemas.
	 */
	initRoleSelect(): void {
		if (!this.isRoleSelect) { return; }

		this.selectData = this.roles.map((role) => {
			return { id: role.id.toString(), text: role.name };
		});

		this.selectConfig = {
			width: '100%',
			placeholder: 'Select role',
		};

		this.selectInitialValue = JSON.parse(JSON.stringify(this.argument.value));

		if (this.parameterSchema.type === 'array') {
			this.selectConfig.placeholder += '(s)';
			this.selectConfig.multiple = true;
			this.selectConfig.allowClear = true;
			this.selectConfig.closeOnSelect = false;
			if (Array.isArray(this.argument.value)) 
				this.selectInitialValue = this.argument.value.map((val: number) => val.toString());
		}
	}

	updateValue($event: any): void {
		this.argument.value = $event;
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

	/**
	 * Event fired on the select2 change for users/roles. Updates the value based on the event value.
	 * @param $event JS Event Fired
	 */
	clearValue(): void {
		this.argument.value = '';
	}

	/**
	 * Adds an item to an array if the argument parameter is array.
	 */
	addItem(): void {
		if (!this.argument.value) this.argument.value = [];

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

	/**
	 * Moves a selected index in an array "up" (by swapping it with the ID before).
	 * @param index Index to move
	 */
	moveUp(index: number): void {
		const idAbove = index - 1;
		const toBeSwapped = (this.argument.value as any[])[idAbove];
		const arrayTypeToBeSwapped = this.arrayTypes[idAbove];

		(this.argument.value as any[])[idAbove] = (this.argument.value as any[])[index];
		(this.argument.value as any[])[index] = toBeSwapped;

		this.arrayTypes[idAbove] = this.arrayTypes[index];
		this.arrayTypes[index] = arrayTypeToBeSwapped;
	}

	/**
	 * Moves a selected index in an array "down" (by swapping it with the ID after).
	 * @param index Index to move
	 */
	moveDown(index: number): void {
		const idBelow = index + 1;
		const toBeSwapped = (this.argument.value as any[])[idBelow];
		const arrayTypeToBeSwapped = this.arrayTypes[idBelow];

		(this.argument.value as any[])[idBelow] = (this.argument.value as any[])[index];
		(this.argument.value as any[])[index] = toBeSwapped;

		this.arrayTypes[idBelow] = this.arrayTypes[index];
		this.arrayTypes[index] = arrayTypeToBeSwapped;
	}

	/**
	 * Removes a value at a given index of the argument value (if the value is an array).
	 * @param index Index to remove
	 */
	removeItem(index: number): void {
		(this.argument.value as any[]).splice(index, 1);
		this.arrayTypes.splice(index, 1);
	}

	/**
	 * Adds a new property to an our argument's value object of a given name and type.
	 */
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

	/**
	 * Removes a property from our argument's value object by key.
	 * @param key Key to remove
	 */
	removeProperty(key: string): void {
		delete (this.argument.value as any)[key];
		delete this.objectTypes[key];
	}

	/**
	 * Track by function for arrays.
	 * Needed to track by index for primitives (since normally it tracks by reference for objects/arrays).
	 * @param index Index to track by
	 * @param item Item in array by index
	 */
	trackArraysBy(index: any, item: any) {
		return index;
	}

	// TODO: maybe somehow recursively find actions that may occur before. Right now it just returns all of them.
	getPreviousActions(): WorkflowNode[] {
		return this.loadedWorkflow.getPreviousActions(this.selectedAction);
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

		if (Array.isArray(schema.items)) {
			(schema.items as GenericObject[]).forEach(i => {
				if (i.type === 'user' || i.type === 'role') { return false; }
			});
		} else if (schema.items && (schema.items.type === 'user' || schema.items.type === 'role')) { return false; }

		return true;
	}

	/**
	 * Checks if this schema represents a user select (single or multiple via array type).
	 * @param schema JSON Schema Object to check against
	 */
	get isUserSelect(): boolean {
		return this.parameterSchema && 
			   (this.parameterSchema.type === 'user' || 
			   (this.parameterSchema.type === 'array' && this.parameterSchema.items && 
			   !Array.isArray(this.parameterSchema.items) && this.parameterSchema.items.type === 'user'));
	}

	/**
	 * Checks if this schema represents a role select (single or multiple via array type).
	 * @param schema JSON Schema Object to check against
	 */
	get isRoleSelect(): boolean {
		return this.parameterSchema &&
			   (this.parameterSchema.type === 'role' || 
			   (this.parameterSchema.type === 'array' && this.parameterSchema.items && 
			   !Array.isArray(this.parameterSchema.items) && this.parameterSchema.items.type === 'role'));
	}

	get isReference(): boolean {
		return [Variant.STATIC_VALUE, Variant.GLOBAL, Variant.WORKFLOW_VARIABLE].indexOf(this.argument.variant) == -1;
	}

	get isStatic(): boolean {
		return this.argument.variant == Variant.STATIC_VALUE;
	}

	get isActionSelect(): boolean {
		return this.argument.variant == Variant.ACTION_RESULT;
	}

	get isVariableSelect(): boolean {
		return this.argument.variant == Variant.WORKFLOW_VARIABLE;
	}

	get isStringSelect(): boolean {
		return this.isStatic && this.parameterSchema && !this.parameterSchema.enum &&
			(this.parameterSchema.type === 'string' || !this.parameterSchema.type);
	}

	get isNumberSelect(): boolean {
		return this.isStatic && this.parameterSchema && (this.parameterSchema.type === 'number' || 
			this.parameterSchema.type === 'integer')
	}

	get isEnumSelect(): boolean {
		return this.isStatic && this.parameterSchema && this.parameterSchema.enum;
	}

	get isBooleanSelect(): boolean {
		return this.isStatic && this.parameterSchema && this.parameterSchema.type === 'boolean';
	}

	get isGlobalSelect() : boolean {
		return this.argument.variant == Variant.GLOBAL;
	}

	addVariable() {
		this.createVariable.emit(this.argument)
	}
}
