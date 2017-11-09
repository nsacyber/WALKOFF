import { Component, ViewEncapsulation, Input } from '@angular/core';

import { PlaybookService } from './playbook.service';

import { Workflow } from '../models/playbook/workflow';
import { AppApi } from '../models/api/appApi';
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
		const api = this.appApis
			.find(a => a.name === this.selectedAppName).transform_apis
			.find(c => c.name === this.selectedTransformApi);
		
		const args: Argument[] = [];
		api.parameters.filter(p => p.name !== api.data_in).forEach((parameterApi) => {
			args.push({
				name: parameterApi.name,
				value: parameterApi.schema.default != null ? parameterApi.schema.default : null,
				reference: '',
				selector: '',
			});
		});

		const newTransform = new Transform();
		newTransform.app = this.selectedAppName;
		newTransform.action = this.selectedTransformApi;
		newTransform.args = args;

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

	getTransformApiArgs(appName: string, transformName: string, argumentName: string): ParameterApi {
		return this.appApis
			.find(a => a.name === appName).transform_apis
			.find(t => t.name === transformName).parameters
			.find(a => a.name === argumentName);
	}

	getTransformNamesForApp(): string[] {
		return this.appApis.find(a => a.name === this.selectedAppName).transform_apis.map(c => c.name);
	}
}
