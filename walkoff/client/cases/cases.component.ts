import { Component, ViewEncapsulation } from '@angular/core';
import { FormControl } from '@angular/forms';
import * as _ from 'lodash';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import { Select2OptionData } from 'ng2-select2';
import 'rxjs/add/operator/debounceTime';

import { CasesService } from './cases.service';

import { CasesModalComponent } from './cases.modal.component';

import { Case } from '../models/case/case';
import { CaseEvent } from '../models/case/caseEvent';
import { CaseNode } from '../models/case/caseNode';
import { AvailableSubscription } from '../models/case/availableSubscription';
import { Playbook } from '../models/playbook/playbook';

interface ICaseHierarchy {
	name: string;
	plural: string;
	prefix?: string;
	children: ICaseHierarchy[];
}

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
	caseHierarchy: ICaseHierarchy = {
		name: 'playbook',
		plural: 'playbooks',
		children: [
			{
				name: 'workflow',
				plural: 'workflows',
				children: [
					{
						name: 'action',
						plural: 'actions',
						children: [
							{
								name: 'trigger',
								plural: 'triggers',
								prefix: 'Trigger: ',
								children: [
									{
										name: 'transform',
										plural: 'transforms',
										prefix: 'Transform: ',
										children: [],
									},
								],
							},
							{
								name: 'branch',
								plural: 'branches',
								prefix: 'Branch: ',
								children: [
									{
										name: 'condition',
										plural: 'conditions',
										prefix: 'Condition: ',
										children: [
											{
												name: 'transform',
												plural: 'transforms',
												prefix: 'Transform: ',
												children: [],
											},
										],
									},
								],
							},
						],
					},
				],
			},
		],
	};

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

	convertPlaybooksToSubscriptionTree(playbooks: Playbook[]): CaseNode {
		const self = this;
		//Top level controller data
		const tree: CaseNode = { name: 'Controller', id: 0, type: 'controller', children: [] };

		// Remap the branches to be under actions as they used to be
		playbooks.forEach(p => {
			p.workflows.forEach(w => {
				w.actions.forEach(a => {
					(a as any).branches = [];
				});

				w.branches.forEach(b => {
					const matchingAction = w.actions.find(s => s.id === b.destination_id);
					if (matchingAction) { (b as any).name = matchingAction.name; }
					(w.actions.find(s => s.id === b.source_id) as any).branches.push(b);
				});

				delete w.branches;
			});
		});

		playbooks.forEach(function (p) {
			tree.children.push(self.getNodeRecursive(p, self.caseHierarchy));
		});
		return tree;
	}

	getNodeRecursive(target: any, hierarchy: ICaseHierarchy): CaseNode {
		const self = this;

		let nodeName = '';
		if (hierarchy.prefix) { nodeName = hierarchy.prefix; }
		//For higher level nodes, use the name
		if (target.name) { 
			nodeName += target.name;
		} else if (target.action_name) {
			nodeName += target.action_name;
		} else { nodeName = '(name unknown)'; }

		const node: CaseNode = { 
			name: nodeName, 
			id: target.id ? target.id : 0, 
			type: hierarchy.name, 
			children: [],
		};
		
		// For each child hierarchy, (most cases only 1 child type), iterate through the child elements
		hierarchy.children.forEach(childHierarchy => {
			target[childHierarchy.plural].forEach((sub: any) => {
				node.children.push(self.getNodeRecursive(sub, childHierarchy));
			});
		});

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
