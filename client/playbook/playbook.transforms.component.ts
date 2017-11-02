import { Component, ViewEncapsulation, ViewChild, ElementRef, Input } from '@angular/core';

import { PlaybookService } from './playbook.service';

import { Workflow } from '../models/playbook/workflow';
import { AppApi } from '../models/api/appApi';
import { TransformApi } from '../models/api/transformApi';
import { ArgumentApi } from '../models/api/argumentApi';
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
	@Input() apps: AppApi[];
	@Input() loadedWorkflow: Workflow;

	selectedTransformApi: string;

	constructor() { }

	ngOnInit(): void {
		this.resetTransformSelection(this.selectedAppName);
	}

	resetTransformSelection(appName: string) {
		let app = this.apps.find(a => a.name === appName);

		if (app.transformApis && app.transformApis.length) this.selectedTransformApi = app.transformApis[0].name;

		console.log(app, this.selectedTransformApi);
	}

	addTransform(): void {
		let api = this.apps.find(a => a.name === this.selectedAppName).transformApis.find(c => c.name === this.selectedTransformApi);
		
		let args: Argument[] = [];
		api.args.forEach((argumentApi) => {
			args.push({
				name: argumentApi.name,
				value: argumentApi.default,
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

	getTransformApiArgs(appName: string, transformName: string, argumentName: string): ArgumentApi {
		return this.apps.find(a => a.name === appName).transformApis.find(t => t.name === transformName).args.find(a => a.name === argumentName);
	}

	getAppsFromApis(): string[] {
		let out: string[] = [];

		this.apps.forEach(app => {
			if (!app.transformApis || !app.transformApis.length) return;
			out.push(app.name);
		});

		return out;
	}

	getTransformNamesForApp(): string[] {
		return this.apps.find(a => a.name === this.selectedAppName).transformApis.map(c => c.name);
	}
}