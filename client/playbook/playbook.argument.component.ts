import { Component, ViewEncapsulation, ViewChild, ElementRef, Input } from '@angular/core';

import { PlaybookService } from './playbook.service';

import { Workflow } from '../models/playbook/workflow';
import { Step } from '../models/playbook/step';
import { ActionApi } from '../models/api/actionApi';
import { ParameterApi } from '../models/api/parameterApi';
import { ParameterSchema } from '../models/api/parameterSchema';
import { Argument } from '../models/playbook/argument';
import { Condition } from '../models/playbook/condition';
import { Transform } from '../models/playbook/transform';

@Component({
	selector: 'playbook-argument-component',
	templateUrl: 'client/playbook/playbook.argument.html',
	styleUrls: [],
	encapsulation: ViewEncapsulation.None,
	providers: [PlaybookService]
})
export class PlaybookArgumentComponent {
	@Input() id: number;
	@Input() argument: Argument;
	@Input() parameterApi: ParameterApi;
	@Input() loadedWorkflow: Workflow;

	// Simple parameter schema reference so I'm not constantly showing parameterApi.schema
	parameterSchema: ParameterSchema;

	constructor() { }

	ngOnInit(): void {
		this.parameterSchema = this.parameterApi.schema;
	}

	// TODO: maybe somehow recursively find steps that may occur before. Right now it just returns all of them.
	getPreviousSteps(): Step[] {
		return this.loadedWorkflow.steps;
	}

	/**
	 * Gets the minimum value to check against for JSON Schema minimum / exclusiveMinimum parameters
	 * @param field JSON Schema object
	 */
	getMin(field: ParameterApi): number {
		if (field.schema.minimum === undefined) return null;
		if (field.schema.exclusiveMinimum) return field.schema.minimum + 1;
		return field.schema.minimum;
	}

	/**
	 * Gets the maximum value to check against for JSON Schema maximum / exclusiveMaximum parameters
	 * @param field JSON Schema Object
	 */
	getMax(field: ParameterApi): number {
		if (field.schema.maximum === undefined) return null;
		if (field.schema.exclusiveMaximum) return field.schema.maximum - 1;
		return field.schema.maximum;
	}
}