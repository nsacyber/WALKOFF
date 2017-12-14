import { Component, ViewEncapsulation } from '@angular/core';
import { FormControl } from '@angular/forms';
import * as _ from 'lodash';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import { Select2OptionData } from 'ng2-select2';
import 'rxjs/add/operator/debounceTime';

import { CasesService } from './cases.service';

import { CasesModalComponent } from './cases.modal.component';

import { Case } from '../models/case';
import { CaseEvent } from '../models/caseEvent';
import { AvailableSubscription } from '../models/availableSubscription';
import { Playbook } from '../models/playbook/playbook';
import { Workflow } from '../models/playbook/workflow';
import { Action } from '../models/playbook/action';
import { Branch } from '../models/playbook/branch';

/**
 * Types as the backend calls them for adding a new CaseEvent.
 */
const types = ['playbook', 'workflow', 'action', 'branch', 'condition', 'transform'];
/**
 * Types that are used to recursively check for the next level. E.g. branches have conditions.
 */
const childrenTypes = ['workflows', 'actions', 'branches', 'conditions', 'transforms'];

@Component({
	selector: 'cases-component',
	templateUrl: 'client/cases/cases.html',
	encapsulation: ViewEncapsulation.None,
	styleUrls: [
		'client/cases/cases.css',
	],
	providers: [CasesService],
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

	constructor(
		private casesService: CasesService, private modalService: NgbModal,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig) {
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
		if (!$event.value || $event.value === '') { return; }
		this.getCaseEvents($event.value);
	}

	filterEvents(): void {
		const searchFilter = this.eventFilterQuery.value ? this.eventFilterQuery.value.toLocaleLowerCase() : '';

		this.displayCaseEvents = this.caseEvents.filter((caseEvent) => {
			return caseEvent.type.toLocaleLowerCase().includes(searchFilter) ||
				caseEvent.message.includes(searchFilter);
		});
	}

	filterCases(): void {
		const searchFilter = this.caseFilterQuery.value ? this.caseFilterQuery.value.toLocaleLowerCase() : '';

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
				this.availableCases = [{ id: '', text: '' }].concat(cases.map((c) => ({ id: c.id.toString(), text: c.name })));
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
		modalRef.componentInstance.subscriptionTree = _.cloneDeep(this.subscriptionTree);

		this._handleModalClose(modalRef);
	}

	editCase(caseToEdit: Case): void {
		const modalRef = this.modalService.open(CasesModalComponent, { windowClass: 'casesModal' });
		modalRef.componentInstance.title = `Edit Case: ${caseToEdit.name}`;
		modalRef.componentInstance.submitText = 'Save Changes';
		modalRef.componentInstance.workingCase = _.cloneDeep(caseToEdit);
		delete modalRef.componentInstance.workingCase.$$index;
		modalRef.componentInstance.availableSubscriptions = this.availableSubscriptions;
		modalRef.componentInstance.subscriptionTree = _.cloneDeep(this.subscriptionTree);

		this._handleModalClose(modalRef);
	}

	deleteCase(caseToDelete: Case): void {
		if (!confirm('Are you sure you want to delete the case "' + caseToDelete.name +
			'"? This will also delete any associated events.')) { return; }

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
		const self = this;
		//Top level controller data
		const tree = { name: 'Controller', uid: 'controller', type: 'controller', children: [] as object[] };

		// Remap the branches to be under actions as they used to be
		playbooks.forEach((p: Playbook) => {
			p.workflows.forEach((w: Workflow) => {
				w.actions.forEach((s: Action) => {
					(s as any).branches = [];
				});

				w.branches.forEach((ns: Branch) => {
					const matchingAction = w.actions.find(s => s.uid === ns.destination_uid);
					if (matchingAction) { (ns as any).name = matchingAction.name; }
					(w.actions.find(s => s.uid === ns.source_uid) as any).branches.push(ns);
				});

				delete w.branches;
			});
		});

		playbooks.forEach(function (p) {
			tree.children.push(self.getNodeRecursive(p, 0));
		});
		return tree;
	}

	getNodeRecursive(target: any, typeIndex: number, prefix?: string): any {
		const self = this;
		// types = ['playbook', 'workflow', 'action', 'branch', 'condition', 'transform'];
		// childrenTypes = ['workflows', 'actions', 'branches', 'conditions', 'transforms'];

		let nodeName = '';
		if (prefix) { nodeName = prefix + ': '; }
		//For higher level nodes, use the name
		if (target.name) { 
			nodeName += target.name;
		} else if (target.action_name) {
			nodeName += target.action_name;
		} else { nodeName = '(name unknown)'; }

		const node = { 
			name: nodeName, 
			uid: target.uid ? target.uid : '', 
			type: types[typeIndex], 
			children: [] as object[],
		};

		const childType = childrenTypes[typeIndex];
		if (childType) {
			let childPrefix: string;

			switch (childType) {
				case 'actions':
					childPrefix = 'Action';
					break;
				case 'branches':
					childPrefix = 'Branch';
					break;
				case 'conditions':
					childPrefix = 'Condition';
					break;
				case 'transforms':
					childPrefix = 'Transform';
					break;
				default:
					childPrefix = '(unknown)';
					break;
			}

			target[childType].forEach(function (sub: any) {
				node.children.push(self.getNodeRecursive(sub, typeIndex + 1, childPrefix));
			});
		}

		if (!node.children.length) { delete node.children; }

		return node;
	}

	getFriendlyArray(input: string[]): string {
		return input.join(', ');
	}

	getFriendlyObject(input: object): string {
		let out = JSON.stringify(input, null, 1);
		out = out.substr(1, out.length - 2).replace(/"/g, '');
		return out;
	}

	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => {
				//Handle modal dismiss
				if (!result || !result.case) { return; }

				//On edit, find and update the edited item
				if (result.isEdit) {
					const toUpdate = _.find(this.cases, c => c.id === result.case.id);
					Object.assign(toUpdate, result.case);

					this.filterCases();

					this.toastyService.success(`Case "${result.case.name}" successfully edited.`);
				} else {
					this.cases.push(result.case);

					this.filterCases();

					this.toastyService.success(`Case "${result.case.name}" successfully added.`);
				}
			},
			(error) => { if (error) { this.toastyService.error(error.message); } });
	}

}
