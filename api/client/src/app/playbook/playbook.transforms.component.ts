import { Component, ViewEncapsulation, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { plainToClass } from 'class-transformer';
import { Workflow } from '../models/playbook/workflow';
import { AppApi } from '../models/api/appApi';
import { TransformApi } from '../models/api/transformApi';
import { ParameterApi } from '../models/api/parameterApi';
import { Argument } from '../models/playbook/argument';
import { Transform } from '../models/playbook/transform';

@Component({
	selector: 'playbook-transforms-component',
	templateUrl: './playbook.transforms.html',
	styleUrls: [],
	encapsulation: ViewEncapsulation.None,
	providers: [],
})
export class PlaybookTransformsComponent implements OnInit {
	@Input() selectedAppName: string;
	@Input() transforms: Transform[];
	@Input() appApis: AppApi[];
	@Input() loadedWorkflow: Workflow;

	@Output() createVariable = new EventEmitter<Argument>();

	selectedTransformApi: string;
	appNamesWithTransforms: string[];

	// tslint:disable-next-line:no-empty
	constructor() { }

	ngOnInit(): void {
		const appsWithTransforms = this.appApis.filter(app => app.transform_apis && app.transform_apis.length);
		
		// If our selected app doesn't have transforms, just auto select the first one
		if (!appsWithTransforms.find(a => a.name === this.selectedAppName)) {
			const firstApp = appsWithTransforms[0];
			if (firstApp) { this.selectedAppName = firstApp.name; }
		}

		this.appNamesWithTransforms = appsWithTransforms.map(app => app.name);

		this.resetTransformSelection(this.selectedAppName);
	}

	/**
	 * Sets/resets the transform selection to the initial transform in the list on load/after adding a transform.
	 * @param appName App name to reset the transforms for
	 */
	resetTransformSelection(appName: string): void {
		const app = this.appApis.find(a => a.name === appName);

		if (app.transform_apis && app.transform_apis.length) { this.selectedTransformApi = app.transform_apis[0].name; }
	}

	/**
	 * Adds a new transform of a given selected app/action to our transforms array.
	 */
	addTransform(): void {
		if (!this.selectedAppName || !this.selectedTransformApi) { return; }

		const newTransform = new Transform();
		newTransform.app_name = this.selectedAppName;
		newTransform.action_name = this.selectedTransformApi;
		// newTransform.arguments = args;

		this.transforms.push(newTransform);
	}

	/**
	 * Moves a selected index in our transforms array "up" (by swapping it with the ID before).
	 * @param index Index to move
	 */
	moveUp(index: number): void {
		const idAbove = index - 1;
		const toBeSwapped = this.transforms[idAbove];

		this.transforms[idAbove] = this.transforms[index];
		this.transforms[index] = toBeSwapped;
	}

	/**
	 * Moves a selected index in our transforms array "down" (by swapping it with the ID after).
	 * @param index Index to move
	 */
	moveDown(index: number): void {
		const idBelow = index + 1;
		const toBeSwapped = this.transforms[idBelow];

		this.transforms[idBelow] = this.transforms[index];
		this.transforms[index] = toBeSwapped;
	}

	/**
	 * Removes a transform from our transforms array by a given index.
	 * @param index Index to remove
	 */
	removeTransform(index: number): void {
		this.transforms.splice(index, 1);
	}

	/**
	 * Returns a TransformApi by app name and condition name.
	 * @param appName App name to find
	 * @param transformName Transform name to find
	 */
	getTransformApi(appName: string, transformName: string): TransformApi {
		const transformApi = this.appApis.find(a => a.name === appName).transform_apis.find(t => t.name === transformName);
		// Filter out the data_in parameter
		transformApi.parameters = transformApi.parameters.filter(p => p.name !== transformApi.data_in);
		return transformApi;
	}

	/**
	 * For a given condition and parameter api, return the argument that already exists (by parameter name),
	 * or create, add, and return an argument with the default values specified in the parameter API.
	 * @param condition Condition to query/mutate
	 * @param parameterApi ParameterApi to use as the basis
	 */
	getOrInitializeArgument(transform: Transform, parameterApi: ParameterApi): Argument {
		// Find an existing argument
		let argument = transform.arguments.find(a => a.name === parameterApi.name);
		if (argument) { return argument; }

		argument = this.getDefaultArgument(parameterApi);
		transform.arguments.push(argument);
		return argument;
	}

	/**
	 * Returns an argument based upon a given parameter API and its default value.
	 * @param parameterApi Parameter API used to generate the default argument
	 */
	getDefaultArgument(parameterApi: ParameterApi): Argument {
		return plainToClass(Argument, {
			name: parameterApi.name,
			value: parameterApi.json_schema.default != null ? parameterApi.json_schema.default : null,
			reference: '',
			selection: '',
		});
	}

	/**
	 * Returns a list of transform names for the selected app name. Used to populate a select.
	 */
	getTransformNamesForApp(): string[] {
		return this.appApis.find(a => a.name === this.selectedAppName).transform_apis.map(c => c.name);
	}

	onCreateVariable(argument: Argument) {
		this.createVariable.emit(argument);
	}
}
