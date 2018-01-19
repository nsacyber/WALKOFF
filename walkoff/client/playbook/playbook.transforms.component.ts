import { Component, ViewEncapsulation, Input } from '@angular/core';

import { PlaybookService } from './playbook.service';

import { Workflow } from '../models/playbook/workflow';
import { AppApi } from '../models/api/appApi';
import { TransformApi } from '../models/api/transformApi';
import { ParameterApi } from '../models/api/parameterApi';
import { Argument } from '../models/playbook/argument';
import { Transform } from '../models/playbook/transform';

@Component({
	selector: 'playbook-transforms-component',
	templateUrl: 'client/playbook/playbook.transforms.html',
	styleUrls: [],
	encapsulation: ViewEncapsulation.None,
	providers: [PlaybookService],
})
export class PlaybookTransformsComponent {
	@Input() selectedAppName: string;
	@Input() transforms: Transform[];
	@Input() appApis: AppApi[];
	@Input() loadedWorkflow: Workflow;

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

	resetTransformSelection(appName: string): void {
		const app = this.appApis.find(a => a.name === appName);

		if (app.transform_apis && app.transform_apis.length) { this.selectedTransformApi = app.transform_apis[0].name; }
	}

	addTransform(): void {
		// const api = this.appApis
		// 	.find(a => a.name === this.selectedAppName).transform_apis
		// 	.find(c => c.name === this.selectedTransformApi);
		
		// const args: Argument[] = [];
		// api.parameters.filter(p => p.name !== api.data_in).forEach((parameterApi) => {
		// 	args.push({
		// 		name: parameterApi.name,
		// 		value: parameterApi.schema.default != null ? parameterApi.schema.default : null,
		// 		reference: '',
		// 		selection: '',
		// 	});
		// });
		if (!this.selectedAppName || !this.selectedTransformApi) { return; }

		const newTransform = new Transform();
		newTransform.app_name = this.selectedAppName;
		newTransform.action_name = this.selectedTransformApi;
		// newTransform.arguments = args;

		this.transforms.push(newTransform);
	}

	moveUp(index: number): void {
		const idAbove = index - 1;
		const toBeSwapped = this.transforms[idAbove];

		this.transforms[idAbove] = this.transforms[index];
		this.transforms[index] = toBeSwapped;
	}

	moveDown(index: number): void {
		const idBelow = index + 1;
		const toBeSwapped = this.transforms[idBelow];

		this.transforms[idBelow] = this.transforms[index];
		this.transforms[index] = toBeSwapped;
	}

	removeTransform(index: number): void {
		this.transforms.splice(index, 1);
	}

	getTransformApi(appName: string, transformName: string): TransformApi {
		const transformApi = this.appApis.find(a => a.name === appName).transform_apis.find(t => t.name === transformName);
		// Filter out the data_in parameter
		transformApi.parameters = transformApi.parameters.filter(p => p.name !== transformApi.data_in);
		return transformApi;
	}

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
		return {
			name: parameterApi.name,
			value: parameterApi.schema.default != null ? parameterApi.schema.default : null,
			reference: 0,
			selection: '',
		};
	}

	getTransformNamesForApp(): string[] {
		return this.appApis.find(a => a.name === this.selectedAppName).transform_apis.map(c => c.name);
	}
}
