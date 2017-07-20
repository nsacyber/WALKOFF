import { Component } from '@angular/core';

import { CasesService } from './cases.service';

import { Case } from '../models/case';

@Component({
	selector: 'cases-component',
	templateUrl: 'client/cases/cases.html',
	styleUrls: [
		'client/cases/cases.css',
	],
	providers: [CasesService]
})
export class CasesComponent {
	cases: Case[];

	constructor(private casesService: CasesService) {

	}

	getCaseSubscriptions(): void {
		this.casesService
			.getCaseSubscriptions()
			.then(caseSubscriptions => this.cases = caseSubscriptions);
	}
}