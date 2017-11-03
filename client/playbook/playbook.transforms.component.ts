import { Component, ViewEncapsulation, ViewChild, ElementRef, Input } from '@angular/core';

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
	providers: [PlaybookService]
})
export class PlaybookTransformsComponent {
	@Input() selectedAppName: string;
	@Input() transforms: Transform[];
	@Input() appApis: AppApi[];
	@Input() loadedWorkflow: Workflow;

	selectedTransformApi: string;
	appNamesWithTransforms: string[];

	constructor() { }

	ngOnInit(): void {
		this.resetTransformSelection(this.selectedAppName);
		this.appNamesWithTransforms = this.appApis.filter(app => app.transform_apis && app.transform_apis.length).map(app => app.name);
	}

	resetTransformSelection(appName: string): void {
		let app = this.appApis.find(a => a.name === appName);

		if (app.transform_apis && app.transform_apis.length) this.selectedTransformApi = app.transform_apis[0].name;

		console.log(app, this.selectedTransformApi);
	}

	addTransform(): void {
		let api = this.appApis.find(a => a.name === this.selectedAppName).transform_apis.find(c => c.name === this.selectedTransformApi);
		
		let args: Argument[] = [];
		api.parameters.filter(p => p.name !== api.dataIn).forEach((parameterApi) => {
			args.push({
				name: parameterApi.name,
				value: parameterApi.schema.default != null ? parameterApi.schema.default : null,
				reference: "",
				selector: ""
			});
		});

		this.transforms.push({
			uid: null,
			app: this.selectedAppName,
			action: this.selectedTransformApi,
			args: args
		});
	}

	moveUp(index: number): void {
		let idAbove = index - 1;
		let toBeSwapped = this.transforms[idAbove];

		this.transforms[idAbove] = this.transforms[index];
		this.transforms[index] = toBeSwapped;
	}

	moveDown(index: number): void {
		let idBelow = index + 1;
		let toBeSwapped = this.transforms[idBelow];

		this.transforms[idBelow] = this.transforms[index];
		this.transforms[index] = toBeSwapped;
	}

	removeTransform(index: number): void {
		this.transforms.splice(index, 1);
	}

	getTransformApiArgs(appName: string, transformName: string, argumentName: string): ParameterApi {
		return this.appApis.find(a => a.name === appName).transform_apis.find(t => t.name === transformName).parameters.find(a => a.name === argumentName);
	}

	getTransformNamesForApp(): string[] {
		return this.appApis.find(a => a.name === this.selectedAppName).transform_apis.map(c => c.name);
	}
}