import { Component, ViewEncapsulation, OnInit } from '@angular/core';
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
	subscriptionType: string;
	arrayPropertyName: string;
	prefix?: string;
	children: ICaseHierarchy[];
	recursivePropertyName?: string;
}

@Component({
	selector: 'cases-component',
	templateUrl: './cases.html',
	encapsulation: ViewEncapsulation.None,
	styleUrls: [
		'./cases.css',
	],
	providers: [CasesService],
})
export class CasesComponent implements OnInit {
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
		subscriptionType: 'playbook',
		arrayPropertyName: 'playbooks',
		children: [
			{
				subscriptionType: 'workflow',
				arrayPropertyName: 'workflows',
				children: [
					{
						subscriptionType: 'action',
						arrayPropertyName: 'actions',
						children: [
							{
								subscriptionType: 'conditional_expression',
								arrayPropertyName: 'trigger',
								prefix: 'Trigger: ',
								recursivePropertyName: 'child_expressions',
								children: [
									{
										subscriptionType: 'condition',
										arrayPropertyName: 'conditions',
										prefix: 'Condition: ',
										children: [
											{
												subscriptionType: 'transform',
												arrayPropertyName: 'transforms',
												prefix: 'Transform: ',
												children: [],
											},
										],
									},
								],
							},
							{
								subscriptionType: 'branch',
								arrayPropertyName: 'branches',
								prefix: 'Branch: ',
								children: [
									{
										subscriptionType: 'conditional_expression',
										arrayPropertyName: 'condition',
										prefix: 'Condition: ',
										recursivePropertyName: 'child_expressions',
										children: [
											{
												subscriptionType: 'condition',
												arrayPropertyName: 'conditions',
												prefix: 'Condition: ',
												children: [
													{
														subscriptionType: 'transform',
														arrayPropertyName: 'transforms',
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
			},
		],
	};

	constructor(
		private casesService: CasesService, private modalService: NgbModal,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {}

	ngOnInit(): void {
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

	/**
	 * Grabs case events from the server for the selected case (from the JS event supplied).
	 * Will update the case events data table with the new case events.
	 * @param event JS event from the select2 case select box
	 */
	caseSelectChange(event: any): void {
		if (!event.value || event.value === '') { return; }
		this.getCaseEvents(event.value);
	}

	/**
	 * Filters case events based upon the input entered into the search filter box above the data table
	 * and compared to various fields on the case event (type, message).
	 */
	filterEvents(): void {
		const searchFilter = this.eventFilterQuery.value ? this.eventFilterQuery.value.toLocaleLowerCase() : '';

		this.displayCaseEvents = this.caseEvents.filter((caseEvent) => {
			return caseEvent.type.toLocaleLowerCase().includes(searchFilter) ||
				caseEvent.message.includes(searchFilter);
		});
	}

	/**
	 * Filters cases based upon the input entered into the search filter box above the data table
	 * and compared to various fields on the case (name, note).
	 */
	filterCases(): void {
		const searchFilter = this.caseFilterQuery.value ? this.caseFilterQuery.value.toLocaleLowerCase() : '';

		this.displayCases = this.cases.filter((c) => {
			return c.name.toLocaleLowerCase().includes(searchFilter) ||
				c.note.includes(searchFilter);
		});
	}

	/**
	 * Grabs all the existing cases in the DB for use in populating the cases datatable.
	 * Will also populate the case select2 data for use on the case events tab.
	 */
	getCases(): void {
		this.casesService
			.getCases()
			.then((cases) => {
				this.displayCases = this.cases = cases;
				this.availableCases = [{ id: '', text: '' }].concat(cases.map(c => ({ id: c.id.toString(), text: c.name })));
			})
			.catch(e => this.toastyService.error(`Error retrieving cases: ${e.message}`));
	}

	/**
	 * Gets an array of case events for a given case ID from the server.
	 * It will then populate our array of case events for display in the case events datatable.
	 * @param caseId CaseId to get events for
	 */
	getCaseEvents(caseId: string | number): void {
		this.casesService
			.getEventsForCase(+caseId)
			.then((caseEvents) => {
				this.displayCaseEvents = this.caseEvents = caseEvents;
				this.filterEvents();
			})
			.catch(e => this.toastyService.error(`Error retrieving events: ${e.message}`));
	}

	/**
	 * Spawns a modal for adding a new case.
	 */
	addCase(): void {
		const modalRef = this.modalService.open(CasesModalComponent, { windowClass: 'casesModal' });
		modalRef.componentInstance.title = 'Add New Case';
		modalRef.componentInstance.submitText = 'Add Case';
		modalRef.componentInstance.workingCase = new Case();
		modalRef.componentInstance.availableSubscriptions = this.availableSubscriptions;
		modalRef.componentInstance.subscriptionTree = _.cloneDeep(this.subscriptionTree);

		this._handleModalClose(modalRef);
	}

	/**
	 * Spawns a modal for editing an existing case.
	 */
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

	/**
	 * After user confirmation, will delete a given case from the database and remove it from our list of cases to display.
	 * @param caseToDelete Case to delete
	 */
	deleteCase(caseToDelete: Case): void {
		if (!confirm('Are you sure you want to delete the case "' + caseToDelete.name +
			'"? This will also delete any associated events.')) { return; }

		this.casesService
			.deleteCase(caseToDelete.id)
			.then(() => {
				this.cases = this.cases.filter(c => c.id !== caseToDelete.id);

				this.filterCases();

				this.toastyService.success(`Case "${caseToDelete.name}" successfully deleted.`);
			})
			.catch(e => this.toastyService.error(e.message));
	}

	/**
	 * Gets a list of available subscriptions from the server,
	 * and then stores it locally for usage within the add/edit modals.
	 */
	getAvailableSubscriptions(): void {
		this.casesService
			.getAvailableSubscriptions()
			.then(availableSubscriptions => this.availableSubscriptions = availableSubscriptions)
			.catch(e => this.toastyService.error(`Error retrieving case subscriptions: ${e.message}`));
	}

	/**
	 * Gets an array of fully populated playbooks from the server,
	 * and then converts them to a subscription tree for usage in the D3 hierarchy tree in add/edit case modal.
	 */
	getPlaybooks(): void {
		this.casesService
			.getPlaybooks()
			.then(playbooks => this.subscriptionTree = this.convertPlaybooksToSubscriptionTree(playbooks))
			.catch(e => this.toastyService.error(`Error retrieving subscription tree: ${e.message}`));
	}

	/**
	 * Converts an array of playbooks to a subscription tree for use in the D3 hierarchy tree in add/edit case modal.
	 * Remaps some of the info to have better visual/logical flow for an end user (e.g. puts branches under actions).
	 * Recursively builds the information based upon the CaseHierarchy object defined on the component.
	 * @param playbooks Array of playbooks to convert
	 */
	convertPlaybooksToSubscriptionTree(playbooks: Playbook[]): CaseNode {
		//Top level controller data
		const tree: CaseNode = { name: 'Controller', id: 'controller', type: 'controller', children: [] };

		playbooks.forEach(playbook => {
			playbook.workflows.forEach(workflow => {
				// Remap the branches to be under actions as they used to be
				// Additionally, put the initial ConditionalExpressions in an array so we can iterate over them
				workflow.actions.forEach(action => {
					(action as any).branches = [];
					
					if (action.trigger) { (action as any).trigger = [action.trigger]; }
				});

				workflow.branches.forEach(branch => {
					const matchingAction = workflow.actions.find(s => s.id === branch.destination_id);
					if (matchingAction) { (branch as any).name = matchingAction.name; }
					(workflow.actions.find(s => s.id === branch.source_id) as any).branches.push(branch);

					if (branch.condition) { (branch as any).condition = [branch.condition]; }
				});
			});
		});

		playbooks.forEach(p => {
			tree.children.push(this.getNodeRecursive(p, this.caseHierarchy));
		});
		return tree;
	}

	/**
	 * Recursively crawls through execution elements based upon a defined ICaseHierarchy.
	 * Returns a hierarchy of CaseNodes to be used in the D3 hierarchy for adding/editing cases.
	 * @param target Target node to convert
	 * @param hierarchy Hierarchy information to handle the conversion
	 */
	getNodeRecursive(target: any, hierarchy: ICaseHierarchy): CaseNode {
		let nodeName = '';
		if (hierarchy.prefix) { nodeName = hierarchy.prefix; }
		//For higher level nodes, use the name
		if (target.name) { 
			nodeName += target.name;
		} else if (target.action_name) {
			nodeName += target.action_name;
		} else if (target.operator) {
			nodeName += target.operator;
		} else { nodeName = '(name unknown)'; }

		const node: CaseNode = { 
			name: nodeName, 
			id: target.id ? target.id : '', 
			type: hierarchy.subscriptionType, 
			children: [],
		};

		// If we're specifying a recursive association (e.g. ConditionalExpressions),
		// iterate through children with the same hierarchical structure
		if (hierarchy.recursivePropertyName) {
			if (Array.isArray(target[hierarchy.recursivePropertyName])) {
				(target[hierarchy.recursivePropertyName] as any[]).forEach(sub => {
					node.children.push(this.getNodeRecursive(sub, hierarchy));
				});
			}
		}
		
		// For each child hierarchy, (most cases only 1 child type), iterate through the child elements
		hierarchy.children.forEach(childHierarchy => {
			if (Array.isArray(target[childHierarchy.arrayPropertyName])) {
				(target[childHierarchy.arrayPropertyName] as any[]).forEach(sub => {
					node.children.push(this.getNodeRecursive(sub, childHierarchy));
				});
			}
		});

		if (!node.children.length) { delete node.children; }

		return node;
	}

	/**
	 * Returns a string of concatenated array values.
	 * E.g. ['some', 'text', 'here'] => 'some, text, here'
	 * @param input Array of strings to concat into a friendly string
	 */
	getFriendlyArray(input: string[]): string {
		return input.join(', ');
	}

	/**
	 * Converts an input object to a JSON string, removing the quotes for better reading.
	 * @param input Input object to convert
	 */
	getFriendlyObject(input: object): string {
		let out = JSON.stringify(input, null, 1);
		out = out.substr(1, out.length - 2).replace(/"/g, '');
		return out;
	}

	/**
	 * On closing an add/edit modal (on clicking save), we will add or update existing cases for display.
	 * @param modalRef ModalRef that is being closed
	 */
	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => {
				//Handle modal dismiss
				if (!result || !result.case) { return; }

				//On edit, find and update the edited item
				if (result.isEdit) {
					const toUpdate = this.cases.find(c => c.id === result.case.id);
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
