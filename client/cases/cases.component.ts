import { Component } from '@angular/core';
import { FormControl } from '@angular/forms';
import * as _ from 'lodash';
import { NgbModal, NgbActiveModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';
import { Select2OptionData } from 'ng2-select2';
import "rxjs/add/operator/debounceTime";

import { CasesService } from './cases.service';

import { CasesModalComponent } from './cases.modal.component';

import { Case } from '../models/case';
import { CaseEvent } from '../models/caseEvent';
import { AvailableSubscription } from '../models/availableSubscription';

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
	availableSubscriptions: AvailableSubscription[] = [];
	caseSelectConfig: Select2Options;
	caseEvents: CaseEvent[] = [];
	displayCases: Case[] = [];
	displayCaseEvents: CaseEvent[] = [];
	eventFilterQuery: FormControl = new FormControl();
	caseFilterQuery: FormControl = new FormControl();

	constructor(private casesService: CasesService, private modalService: NgbModal, private toastyService: ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';

		this.caseSelectConfig = {
			width: '100%',
			placeholder: 'Select a Case to view its Events',
			allowClear: true,
		};

		this.getCases();
		this.getAvailableSubscriptions();

		this.eventFilterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterEvents());

		this.caseFilterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterCases());
	}

	caseSelectChange($event: any): void {
		if (!$event.value || $event.value === '') return;
		console.log($event.value);
		this.getCaseEvents($event.value);
	}

	filterEvents(): void {
		let searchFilter = this.eventFilterQuery.value ? this.eventFilterQuery.value.toLocaleLowerCase() : '';

		this.displayCaseEvents = this.caseEvents.filter((caseEvent) => {
			return caseEvent.type.toLocaleLowerCase().includes(searchFilter) ||
				caseEvent.message.includes(searchFilter);
		});
	}

	filterCases(): void {
		let searchFilter = this.caseFilterQuery.value ? this.caseFilterQuery.value.toLocaleLowerCase() : '';

		this.displayCases = this.cases.filter((c) => {
			return c.name.toLocaleLowerCase().includes(searchFilter) ||
				c.note.includes(searchFilter);
		});
	}

	getCases(): void {
		this.casesService
			.getCases()
			.then((cases) => {
				this.displayCases = this.cases = cases;
				this.availableCases = [{ id: '', text: '' }].concat(cases.map((c) => { return { id: c.id.toString(), text: c.name } }));
			})
			.catch(e => this.toastyService.error(`Error retrieving cases: ${e.message}`));
	}

	getCaseEvents(caseName: string): void {
		this.casesService
			.getEventsForCase(caseName)
			.then((caseEvents) => {
				this.displayCaseEvents = this.caseEvents = caseEvents;
				this.filterEvents();
			})
			.catch(e => this.toastyService.error(`Error retrieving events: ${e.message}`));
	}

	addCase(): void {
		const modalRef = this.modalService.open(CasesModalComponent, { windowClass: 'casesModal' });
		modalRef.componentInstance.title = 'Add New Case';
		modalRef.componentInstance.submitText = 'Add Case';
		modalRef.componentInstance.workingCase = new Case();
		modalRef.componentInstance.availableSubscriptions = this.availableSubscriptions;

		this._handleModalClose(modalRef);
	}

	editCase(caseToEdit: Case): void {
		const modalRef = this.modalService.open(CasesModalComponent, { windowClass: 'casesModal' });
		modalRef.componentInstance.title = `Edit Case: ${caseToEdit.name}`;
		modalRef.componentInstance.submitText = 'Save Changes';
		modalRef.componentInstance.workingCase = _.cloneDeep(caseToEdit);
		modalRef.componentInstance.availableSubscriptions = this.availableSubscriptions;

		this._handleModalClose(modalRef);
	}

	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => {
				//Handle modal dismiss
				if (!result || !result.case) return;

				//On edit, find and update the edited item
				if (result.isEdit) {
					let toUpdate = _.find(this.cases, c => c.id === result.case.id);
					Object.assign(toUpdate, result.case);

					this.filterCases();

					this.toastyService.success(`Case "${result.case.name}" successfully edited.`);
				}
				//On add, push the new item
				else {
					this.cases.push(result.case);

					this.filterCases();

					this.toastyService.success(`Case "${result.case.name}" successfully added.`);
				}
			},
			(error) => { if (error) this.toastyService.error(error.message); });
	}

	deleteCase(caseToDelete: Case): void {
		if (!confirm(`Are you sure you want to delete the case "${caseToDelete.name}"? This will also delete any associated events.`)) return;

		this.casesService
			.deleteCase(caseToDelete.id)
			.then(() => {
				this.cases = _.reject(this.cases, c => c.id === caseToDelete.id);

				this.filterCases();

				this.toastyService.success(`Case "${caseToDelete.name}" successfully deleted.`);
			})
			.catch(e => this.toastyService.error(e.message));
	}

	getAvailableSubscriptions(): void {
		this.casesService
			.getAvailableSubscriptions()
			.then(availableSubscriptions => this.availableSubscriptions = availableSubscriptions)
			.catch(e => this.toastyService.error(`Error retrieving case subscriptions: ${e.message}`));
	}

	getFriendlyArray(input: string[]): string {
		return input.join(', ');
	}

	getFriendlyObject(input: Object): string {
		return JSON.stringify(input, undefined, 2);
	}
}