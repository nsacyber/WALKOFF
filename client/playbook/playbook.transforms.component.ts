import { Component, ViewEncapsulation, ViewChild, ElementRef, Input } from '@angular/core';

import { PlaybookService } from './playbook.service';

import { Workflow } from '../models/playbook/workflow';
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
	@Input() appName: string;
	@Input() transforms: Transform[];
	@Input() transformApis: TransformApi[];
	@Input() loadedWorkflow: Workflow;

	selectedTransformApi: string = this.transformApis[0].name;

	constructor() { }

	addTransform(): void {
		let api = this.transformApis.find(t => t.name === this.selectedTransformApi);

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
			app: this.appName,
			action: api.name,
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

	getTransformApiArgs(transformName: string, argumentName: string): ArgumentApi {
		return this.transformApis.find(t => t.name === transformName).args.find(a => a.name === argumentName);
	}
}