import { Component, ViewEncapsulation, Input } from '@angular/core';

import { PlaybookService } from './playbook.service';

import { Workflow } from '../models/playbook/workflow';
import { Action } from '../models/playbook/action';
import { ParameterApi } from '../models/api/parameterApi';
import { ParameterSchema } from '../models/api/parameterSchema';
import { Argument } from '../models/playbook/argument';
import { GenericObject } from '../models/genericObject';

const AVAILABLE_TYPES = ['string', 'number', 'boolean'];

@Component({
	selector: 'playbook-argument-component',
	templateUrl: 'client/playbook/playbook.argument.html',
	styleUrls: [],
	encapsulation: ViewEncapsulation.None,
	providers: [PlaybookService],
})
export class PlaybookArgumentComponent {
	@Input() id: number;
	@Input() argument: Argument;
	@Input() parameterApi: ParameterApi;
	@Input() loadedWorkflow: Workflow;

	propertyName: string = '';
	selectedType: string;
	availableTypes: string[] = AVAILABLE_TYPES;
	arrayTypes: string[] = [];
	objectTypes: GenericObject = {};
	// Simple parameter schema reference so I'm not constantly showing parameterApi.schema
	parameterSchema: ParameterSchema;

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
}
