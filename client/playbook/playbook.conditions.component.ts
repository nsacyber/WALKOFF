import { Component, ViewEncapsulation, Input } from '@angular/core';

import { PlaybookService } from './playbook.service';

import { AppApi } from '../models/api/appApi';
import { ConditionApi } from '../models/api/conditionApi';
import { ParameterApi } from '../models/api/parameterApi';
import { Workflow } from '../models/playbook/workflow';
import { Argument } from '../models/playbook/argument';
import { Condition } from '../models/playbook/condition';

@Component({
	selector: 'playbook-conditions-component',
	templateUrl: 'client/playbook/playbook.conditions.html',
	styleUrls: [],
	encapsulation: ViewEncapsulation.None,
	providers: [PlaybookService],
})
export class PlaybookConditionsComponent {
	@Input() selectedAppName: string;
	@Input() conditions: Condition[];
	@Input() appApis: AppApi[];
	@Input() loadedWorkflow: Workflow;

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

	resetConditionSelection(appName: string) {
		const app = this.appApis.find(a => a.name === appName);

		if (app.condition_apis && app.condition_apis.length) { this.selectedConditionApi = app.condition_apis[0].name; }
	}

	addCondition(): void {
		// const api = this.appApis
		// 	.find(a => a.name === this.selectedAppName).condition_apis
		// 	.find(c => c.name === this.selectedConditionApi);

		// const args: Argument[] = [];
		// // Omit the parameter that matches the data_in
		// api.parameters.filter(p => p.name !== api.data_in).forEach((parameterApi) => {
		// 	args.push({
		// 		name: parameterApi.name,
		// 		value: parameterApi.schema.default != null ? parameterApi.schema.default : null,
		// 		reference: '',
		// 		selection: '',
		// 	});
		// });

		const newCondition = new Condition();
		newCondition.app_name = this.selectedAppName;
		newCondition.action_name = this.selectedConditionApi;
		// newCondition.arguments = [];

		this.conditions.push(newCondition);
	}

	moveUp(index: number): void {
		const idAbove = index - 1;
		const toBeSwapped = this.conditions[idAbove];

		this.conditions[idAbove] = this.conditions[index];
		this.conditions[index] = toBeSwapped;
	}

	moveDown(index: number): void {
		const idBelow = index + 1;
		const toBeSwapped = this.conditions[idBelow];

		this.conditions[idBelow] = this.conditions[index];
		this.conditions[index] = toBeSwapped;
	}

	removeCondition(index: number): void {
		this.conditions.splice(index, 1);
	}

	getConditionApi(appName: string, conditionName: string): ConditionApi {
		const conditionApi = this.appApis.find(a => a.name === appName).condition_apis.find(c => c.name === conditionName);
		// Filter out the data_in parameter
		conditionApi.parameters = conditionApi.parameters.filter(p => p.name !== conditionApi.data_in);
		return conditionApi;
	}

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
		return {
			name: parameterApi.name,
			value: parameterApi.schema.default != null ? parameterApi.schema.default : null,
			reference: '',
			selection: '',
		};
	}

	getConditionNamesForApp(): string[] {
		return this.appApis.find(a => a.name === this.selectedAppName).condition_apis.map(c => c.name);
	}
}
