import { Component, ViewEncapsulation, ViewChild, ElementRef, Input } from '@angular/core';

import { PlaybookService } from './playbook.service';

import { App } from '../models/api/app';
import { ConditionApi } from '../models/api/conditionApi';
import { TransformApi } from '../models/api/transformApi';
import { ArgumentApi } from '../models/api/argumentApi';
import { Workflow } from '../models/playbook/workflow';
import { Argument } from '../models/playbook/argument';
import { Condition } from '../models/playbook/condition';
import { Transform } from '../models/playbook/transform';

@Component({
	selector: 'playbook-conditions-component',
	templateUrl: 'client/playbook/playbook.conditions.html',
	styleUrls: [],
	encapsulation: ViewEncapsulation.None,
	providers: [PlaybookService]
})
export class PlaybookConditionsComponent {
	@Input() selectedAppName: string;
	@Input() conditions: Condition[];
	@Input() apps: App[];
	// @Input() conditionApis: ConditionApi[];
	// @Input() transformApis: TransformApi[];
	@Input() loadedWorkflow: Workflow;

	selectedConditionApi: string;

	constructor() { }

	ngOnInit() {
		this.resetConditionSelection(this.selectedAppName);
	}

	resetConditionSelection(appName: string) {
		let app = this.apps.find(a => a.name === appName);

		if (app.conditionApis && app.conditionApis.length) this.selectedConditionApi = app.conditionApis[0].name;
	}

	addCondition(): void {
		let api = this.apps.find(a => a.name === this.selectedAppName).conditionApis.find(c => c.name === this.selectedConditionApi);

		let args: Argument[] = [];
		api.args.forEach((argumentApi) => {
			args.push({
				name: argumentApi.name,
				value: argumentApi.default,
				reference: "",
				selector: ""
			});
		});

		this.conditions.push({
			uid: null,
			app: this.selectedAppName,
			action: this.selectedConditionApi,
			args: args,
			transforms: []
		});
	}

	getConditionApiArgs(appName: string, conditionName: string, argumentName: string): ArgumentApi {
		return this.apps.find(a => a.name === appName).conditionApis.find(c => c.name === conditionName).args.find(a => a.name === argumentName);
	}

	getAppsFromApis(): string[] {
		let out: string[] = [];

		this.apps.forEach(app => {
			if (!app.conditionApis || !app.conditionApis.length) return;
			out.push(app.name);
		});

		return out;
	}

	getConditionNamesForApp(): string[] {
		return this.apps.find(a => a.name === this.selectedAppName).conditionApis.map(c => c.name);
	}
}