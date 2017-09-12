import { Component, ViewEncapsulation } from '@angular/core';
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

const types = ['playbook', 'workflow', 'step', 'nextstep', 'flag', 'filter'];
const childrenTypes = ['workflows', 'steps', 'next', 'flags', 'filters'];

@Component({
	selector: 'cases-component',
	templateUrl: 'client/cases/cases.html',
	encapsulation: ViewEncapsulation.None,
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
	subscriptionTree: any;

	constructor(private casesService: CasesService, private modalService: NgbModal, private toastyService: ToastyService, private toastyConfig: ToastyConfig) {		
		this.toastyConfig.theme = 'bootstrap';

		this.caseSelectConfig = {
			width: '100%',
			placeholder: 'Select a Case to view its Events',
		};

		this.getCases();
		this.getAvailableSubscriptions();
		this.getPlaybooks();

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
		modalRef.componentInstance.subscriptionTree = this.subscriptionTree;

		this._handleModalClose(modalRef);
	}

	editCase(caseToEdit: Case): void {
		const modalRef = this.modalService.open(CasesModalComponent, { windowClass: 'casesModal' });
		modalRef.componentInstance.title = `Edit Case: ${caseToEdit.name}`;
		modalRef.componentInstance.submitText = 'Save Changes';
		modalRef.componentInstance.workingCase = _.cloneDeep(caseToEdit);
		delete modalRef.componentInstance.workingCase.$$index;
		modalRef.componentInstance.availableSubscriptions = this.availableSubscriptions;
		modalRef.componentInstance.subscriptionTree = this.subscriptionTree;
		console.log(modalRef.componentInstance.workingCase);

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

	getPlaybooks(): void {
		this.casesService
			.getPlaybooks()
			.then(playbooks => this.subscriptionTree = this.convertPlaybooksToSubscriptionTree(playbooks))
			.catch(e => this.toastyService.error(`Error retrieving subscription tree: ${e.message}`));
	}

	convertPlaybooksToSubscriptionTree(playbooks: any[]): any {
		let self = this;
		//Top level controller data
		let tree = { name: 'Controller', uid: 'controller', type: 'controller', children: <Object[]>[] };

		playbooks.forEach(function (p) {
			tree.children.push(self.getNodeRecursive(p, 0));
			// let node = { name: p.name, uid: '', type: 'playbook', children: <any>[] }

			// p.workflows.forEach(function (w: any) {
			// 	let node = { name: w.name, uid: w.uid, type: 'workflow', chilren: <any>[] };



			// 	p.children.push(node);
			// })

			// tree.children.push(node);
		});
		console.log(tree);
		return tree;
	}

	getNodeRecursive(target: any, typeIndex: number, prefix?: string): any {
		let self = this;
		// types = ['playbook', 'workflow', 'step', 'nextstep', 'flag', 'filter'];
		// childrenTypes = ['workflows', 'steps', 'next', 'flags', 'filters'];

		let nodeName = '';
		if (prefix) nodeName = prefix + ': ';
		//For higher level nodes, use the name
		if (target.name) nodeName += target.name;
		//For lower level nodes such as flag and filter, use action
		else if (target.action) nodeName += target.action;
		else nodeName = '(name unknown)';

		let node = { 
			name: nodeName, 
			uid: target.uid ? target.uid : '', 
			type: types[typeIndex], 
			children: <Object[]>[]
		};

		let childType = childrenTypes[typeIndex];
		if (childType) {
			let prefix: string;

			switch (childType) {
				case 'steps':
					prefix = 'Step';
					break;
				case 'next':
					prefix = 'Next Step';
					break;
				case 'flags':
					prefix = 'Flag';
					break;
				case 'filters':
					prefix = 'Filter';
					break;
			}

			target[childType].forEach(function (sub: any) {
				node.children.push(self.getNodeRecursive(sub, typeIndex + 1, prefix));
			});
		}

		if (!node.children.length) delete node.children;

		return node;
	}

	getFriendlyArray(input: string[]): string {
		return input.join(', ');
	}

	getFriendlyObject(input: Object): string {
		return JSON.stringify(input, undefined, 2);
	}
}