import { Component, ViewEncapsulation, Input, Output, EventEmitter, OnInit } from '@angular/core';
import { plainToClass } from 'class-transformer';
import { AppApi } from '../models/api/appApi';
import { ConditionApi } from '../models/api/conditionApi';
import { ParameterApi } from '../models/api/parameterApi';
import { Workflow } from '../models/playbook/workflow';
import { Argument } from '../models/playbook/argument';
import { Condition } from '../models/playbook/condition';


@Component({
	selector: 'playbook-conditions-component',
	templateUrl: './playbook.conditions.html',
	styleUrls: [],
	encapsulation: ViewEncapsulation.None,
	providers: [],
})
export class PlaybookConditionsComponent implements OnInit {
	@Input() selectedAppName: string;
	@Input() conditions: Condition[];
	@Input() appApis: AppApi[];
	@Input() loadedWorkflow: Workflow;

	@Output() createVariable = new EventEmitter<Argument>();

	selectedConditionApi: string;
	appNamesWithConditions: string[];

	// tslint:disable-next-line:no-empty
	constructor() { }

	ngOnInit() {
		const appsWithConditions = this.appApis.filter(app => app.condition_apis && app.condition_apis.length);

		// If our selected app doesn't have conditions, just auto select the first one
		if (!appsWithConditions.find(a => a.name === this.selectedAppName)) {
			const firstApp = appsWithConditions[0];
			if (firstApp) { this.selectedAppName = firstApp.name; }
		}

		this.appNamesWithConditions = appsWithConditions.map(app => app.name);

		this.resetConditionSelection(this.selectedAppName);
	}

	/**
	 * Sets/resets the condition selection to the initial condition in the list on load/after adding a condition.
	 * @param appName App name to reset the conditions for
	 */
	resetConditionSelection(appName: string) {
		const app = this.appApis.find(a => a.name === appName);

		if (app.condition_apis && app.condition_apis.length) { this.selectedConditionApi = app.condition_apis[0].name; }
	}

	/**
	 * Adds a new condition of a given selected app/action to our conditions array.
	 */
	addCondition(): void {
		if (!this.selectedAppName || !this.selectedConditionApi) { return; }

		const newCondition = new Condition();
		newCondition.app_name = this.selectedAppName;
		newCondition.action_name = this.selectedConditionApi;
		// newCondition.arguments = [];

		this.conditions.push(newCondition);
	}

	/**
	 * Moves a selected index in our conditions array "up" (by swapping it with the ID before).
	 * @param index Index to move
	 */
	moveUp(index: number): void {
		const idAbove = index - 1;
		const toBeSwapped = this.conditions[idAbove];

		this.conditions[idAbove] = this.conditions[index];
		this.conditions[index] = toBeSwapped;
	}

	/**
	 * Moves a selected index in our conditions array "down" (by swapping it with the ID after).
	 * @param index Index to move
	 */
	moveDown(index: number): void {
		const idBelow = index + 1;
		const toBeSwapped = this.conditions[idBelow];

		this.conditions[idBelow] = this.conditions[index];
		this.conditions[index] = toBeSwapped;
	}

	/**
	 * Removes a condition from our conditions array by a given index.
	 * @param index Index to remove
	 */
	removeCondition(index: number): void {
		this.conditions.splice(index, 1);
	}

	/**
	 * Returns a ConditionApi by app name and condition name.
	 * @param appName App name to find
	 * @param conditionName Condition name to find
	 */
	getConditionApi(appName: string, conditionName: string): ConditionApi {
		const conditionApi = this.appApis.find(a => a.name === appName).condition_apis.find(c => c.name === conditionName);
		// Filter out the data_in parameter
		conditionApi.parameters = conditionApi.parameters.filter(p => p.name !== conditionApi.data_in);
		return conditionApi;
	}

	/**
	 * For a given condition and parameter api, return the argument that already exists (by parameter name),
	 * or create, add, and return an argument with the default values specified in the parameter API.
	 * @param condition Condition to query/mutate
	 * @param parameterApi ParameterApi to use as the basis
	 */
	getOrInitializeArgument(condition: Condition, parameterApi: ParameterApi): Argument {
		// Find an existing argument
		let argument = condition.arguments.find(a => a.name === parameterApi.name);
		if (argument) { return argument; }

		argument = this.getDefaultArgument(parameterApi);
		condition.arguments.push(argument);
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
	 * Returns a list of condition names for the selected app name. Used to populate a select.
	 */
	getConditionNamesForApp(): string[] {
		return this.appApis.find(a => a.name === this.selectedAppName).condition_apis.map(c => c.name);
	}

	onCreateVariable(argument: Argument) {
		this.createVariable.emit(argument);
	}
}
