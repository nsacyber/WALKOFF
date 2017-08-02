import { Component } from '@angular/core';
import { FormControl } from '@angular/forms';
import { Select2OptionData } from 'ng2-select2';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';

import { CasesService } from './cases.service';

import { Case } from '../models/case';
import { CaseEvent } from '../models/caseEvent';

@Component({
	selector: 'cases-component',
	templateUrl: 'client/cases/cases.html',
	styleUrls: [
		'client/cases/cases.css',
	],
	providers: [CasesService]
})
export class CasesComponent {
	cases: Case[] = [];
	availableCases: Select2OptionData[] = [];
	caseSelectConfig: Select2Options;
	caseEvents: CaseEvent[] = [];
	displayCaseEvents: CaseEvent[] = [];
	filterQuery: FormControl = new FormControl();

	constructor(private casesService: CasesService, private toastyService:ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';

		this.caseSelectConfig = {
			width: '100%',
			placeholder: 'Select a Case to view its Events',
			allowClear: true,
		};

		this.getCases();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterEvents());
	}

	caseSelectChange($event: any): void {
		if (!$event.value || $event.value === '') return;
		
		this.casesService
			.getEventsForCase($event.value)
			.then((caseEvents) => {
				this.displayCaseEvents = this.caseEvents = caseEvents;
				this.filterEvents();
			})
			.catch(e => this.toastyService.error(`Error retrieving events: ${e.message}`));
	}

	filterEvents(): void {
		if (!this.caseEvents.length) return;

		let searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayCaseEvents = this.caseEvents.filter((caseEvent) => {
			return caseEvent.type.toLocaleLowerCase().includes(searchFilter) ||
				caseEvent.message.includes(searchFilter);
		});
	}

	getCases(): void {
		this.casesService
			.getCases()
			.then((cases) => {
				this.cases = cases;
				this.availableCases = [{ id: '', text: ''}].concat(cases.map((c) => { return { id: c.name, text: c.name } }));
			})
			.catch(e => this.toastyService.error(`Error retrieving cases: ${e.message}`));
	}

	getCaseSubscriptions(): void {
		this.casesService
			.getCaseSubscriptions()
			.then(caseSubscriptions => this.cases = caseSubscriptions)
			.catch(e => this.toastyService.error(`Error retrieving case subscriptions: ${e.message}`));
	}

	getFriendlyArray(input: string[]): string {
		return input.join(', ');
	}

	getFriendlyObject(input: Object): string {
		return JSON.stringify(input, undefined, 2);
	}
}