import { Component } from '@angular/core';

import { CasesService } from './cases.service';

import { Case } from '../controller/case';

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

	notifyMe() : void {
		if (!Notification) {
			console.log('Desktop notifications not available in your browser. Try Chromium.');
		}
		else if (Notification.permission !== "granted") Notification.requestPermission();
		else {
			var notification = new Notification('WALKOFF event', {
				icon: 'http://cdn.sstatic.net/stackexchange/img/logos/so/so-icon.png',
				body: "workflow was executed!",
			});

			notification.onclick = function () {
				window.open("https://github.com/iadgov");
			};
		}
	}
}