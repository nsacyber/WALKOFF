import { Component, ViewEncapsulation, ViewChild, ElementRef, Input } from '@angular/core';

import { PlaybookService } from './playbook.service';

import { Workflow } from '../models/playbook/workflow';
import { ActionApi } from '../models/api/actionApi';
import { ArgumentApi } from '../models/api/argumentApi';
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
	@Input() argumentApi: ArgumentApi;
	@Input() loadedWorkflow: Workflow;

	constructor() { }

	// TODO: maybe somehow recursively find steps that may occur before. Right now it just returns all of them.
	getPreviousSteps() {
		return this.loadedWorkflow.steps;
	}

	/**
	 * Gets the minimum value to check against for JSON Schema minimum / exclusiveMinimum parameters
	 * @param field JSON Schema object
	 */
	getMin(field: any) {
		if (field.minimum === undefined) return null;
		if (field.exclusiveMinimum) return field.minimum + 1;
		return field.minimum;
	}

	/**
	 * Gets the maximum value to check against for JSON Schema maximum / exclusiveMaximum parameters
	 * @param field JSON Schema Object
	 */
	getMax(field: any) {
		if (field.maximum === undefined) return null;
		if (field.exclusiveMaximum) return field.maximum - 1;
		return field.maximum;
	}
}