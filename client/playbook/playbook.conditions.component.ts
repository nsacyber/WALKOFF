import { Component, ViewEncapsulation, ViewChild, ElementRef, Input } from '@angular/core';

import { PlaybookService } from './playbook.service';

import { Workflow } from '../models/playbook/workflow';
import { ConditionApi } from '../models/api/conditionApi';
import { TransformApi } from '../models/api/transformApi';
import { ArgumentApi } from '../models/api/argumentApi';
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
	@Input() appName: string;
	@Input() conditions: Condition[];
	@Input() conditionApis: ConditionApi[];
	@Input() transformApis: TransformApi[];
	@Input() loadedWorkflow: Workflow;

	selectedConditionApi: string = this.conditionApis[0].name;

	constructor() { }

	addCondition(): void {
		let api = this.conditionApis.find(c => c.name === this.selectedConditionApi);

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
			app: this.appName,
			action: api.name,
			args: args,
			transforms: []
		});
	}

	getConditionApiArgs(conditionName: string, argumentName: string): ArgumentApi {
		return this.conditionApis.find(c => c.name === conditionName).args.find(a => a.name === argumentName);
	}
}