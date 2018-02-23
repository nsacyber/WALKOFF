import { Component, ViewEncapsulation, OnInit, AfterViewChecked, ElementRef, ViewChild,
	ChangeDetectorRef } from '@angular/core';
import { FormControl } from '@angular/forms';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import { Select2OptionData } from 'ng2-select2';
import { DatatableComponent } from '@swimlane/ngx-datatable';
import 'rxjs/add/operator/debounceTime';

import { ExecutionService } from './execution.service';
import { AuthService } from '../auth/auth.service';

import { WorkflowStatus } from '../models/execution/workflowStatus';
import { WorkflowStatusEvent } from '../models/execution/workflowStatusEvent';
import { Workflow } from '../models/playbook/workflow';
import { ActionStatusEvent } from '../models/execution/actionStatusEvent';
import { Argument } from '../models/playbook/argument';
import { GenericObject } from '../models/genericObject';
import { CurrentAction } from '../models/execution/currentAction';

@Component({
	selector: 'execution-component',
	templateUrl: './execution.html',
	styleUrls: [
		'./execution.css',
	],
	encapsulation: ViewEncapsulation.None,
	providers: [ExecutionService, AuthService],
})
export class ExecutionComponent implements OnInit, AfterViewChecked {
	@ViewChild('actionStatusContainer') actionStatusContainer: ElementRef;
	@ViewChild('actionStatusTable') actionStatusTable: DatatableComponent;

	schedulerStatus: string;
	workflowStatuses: WorkflowStatus[] = [];
	displayWorkflowStatuses: WorkflowStatus[] = [];
	workflows: Workflow[] = [];
	availableWorkflows: Select2OptionData[] = [];
	workflowSelectConfig: Select2Options;
	selectedWorkflow: Workflow;
	loadedWorkflowStatus: WorkflowStatus;
	actionStatusComponentWidth: number;
	workflowStatusActions: GenericObject;

	filterQuery: FormControl = new FormControl();

	constructor(
		private executionService: ExecutionService, private authService: AuthService, private cdr: ChangeDetectorRef,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {}

	/**
	 * On component init, set up our workflow select2 config.
	 * Also get workflows to select, workflow statuses to display in the datatable.
	 * Set up SSEs for workflow status and action status to add/update data in our datatables.
	 */
	ngOnInit(): void {
		this.toastyConfig.theme = 'bootstrap';

		this.workflowSelectConfig = {
			width: '100%',
			placeholder: 'Select a Workflow',
		};
		this.workflowStatusActions = {
			resume: 'resume',
			pause: 'pause',
			abort: 'abort',
		};

		this.getWorkflows();
		this.getWorkflowStatuses();
		this.getWorkflowStatusSSE();
		this.getActionStatusSSE();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterWorkflowStatuses());
	}

	/**
	 * This angular function is used primarily to recalculate column widths for execution results table.
	 */
	ngAfterViewChecked(): void {
		// Check if the table size has changed, and recalculate.
		if (this.actionStatusTable && this.actionStatusTable.recalculate && 
			(this.actionStatusContainer.nativeElement.clientWidth !== this.actionStatusComponentWidth)) {
			this.actionStatusComponentWidth = this.actionStatusContainer.nativeElement.clientWidth;
			this.actionStatusTable.recalculate();
			this.cdr.detectChanges();
		}
	}

	/**
	 * Filters out the workflow statuses based on the value in the search/filter box.
	 * Checks against various parameters on the workflow statuses to set our display workflow statuses.
	 */
	filterWorkflowStatuses(): void {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayWorkflowStatuses = this.workflowStatuses.filter((s) => {
			return s.name.toLocaleLowerCase().includes(searchFilter) ||
				s.status.toLocaleLowerCase().includes(searchFilter) ||
				(s.current_action &&
					(s.current_action.name.toLocaleLowerCase().includes(searchFilter) ||
					s.current_action.action_name.toLocaleLowerCase().includes(searchFilter) ||
					s.current_action.app_name.toLocaleLowerCase().includes(searchFilter)));
		});
	}

	/**
	 * Gets a list of workflow statuses from the server for initial population.
	 */
	getWorkflowStatuses(): void {
		this.executionService
			.getWorkflowStatusList()
			.then(workflowStatuses => this.displayWorkflowStatuses = this.workflowStatuses = workflowStatuses)
			.catch(e => this.toastyService.error(`Error retrieving workflow statuses: ${e.message}`));
	}

	/**
	 * Initiates an EventSource for workflow statuses from the server. Binds various events to the event handler.
	 */
	getWorkflowStatusSSE(): void {
		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				const eventSource = new (window as any)
					.EventSource(`api/streams/workflowqueue/workflow_status?access_token=${authToken}`);

				eventSource.addEventListener('queued', (e: any) => this.workflowStatusEventHandler(e));
				eventSource.addEventListener('started', (e: any) => this.workflowStatusEventHandler(e));
				eventSource.addEventListener('paused', (e: any) => this.workflowStatusEventHandler(e));
				eventSource.addEventListener('resumed', (e: any) => this.workflowStatusEventHandler(e));
				eventSource.addEventListener('awaiting_data', (e: any) => this.workflowStatusEventHandler(e));
				eventSource.addEventListener('triggered', (e: any) => this.workflowStatusEventHandler(e));
				eventSource.addEventListener('aborted', (e: any) => this.workflowStatusEventHandler(e));
				eventSource.addEventListener('completed', (e: any) => this.workflowStatusEventHandler(e));

				eventSource.onerror = (err: Error) => {
					console.error(err);
				};
			});
	}

	/**
	 * Handles an EventSource message for Workflow Status. 
	 * Updates existing workflow statuses for status updates or adds new ones to the list for display.
	 * @param message EventSource message for workflow status
	 */
	workflowStatusEventHandler(message: any): void {
		const workflowStatusEvent: WorkflowStatusEvent = JSON.parse(message.data);

		const matchingWorkflowStatus = this.workflowStatuses.find(ws => ws.execution_id === workflowStatusEvent.execution_id);

		if (matchingWorkflowStatus) {
			matchingWorkflowStatus.status = workflowStatusEvent.status;

			switch (message.type) {
				case 'queued':
					// shouldn't happen
					break;
				case 'started':
					matchingWorkflowStatus.started_at = workflowStatusEvent.timestamp;
					matchingWorkflowStatus.current_action = workflowStatusEvent.current_action;
					break;
				case 'paused':
				case 'resumed':
				case 'awaiting_data':
				case 'triggered':
					matchingWorkflowStatus.current_action = workflowStatusEvent.current_action;
					break;
				case 'aborted':
				case 'completed':
					matchingWorkflowStatus.completed_at = workflowStatusEvent.timestamp;
					delete matchingWorkflowStatus.current_action;
					break;
				default:
					this.toastyService.warning(`Unknown Workflow Status SSE Type: ${message.type}.`);
					break;
			}
		} else {
			this.workflowStatuses.push(workflowStatusEvent.toNewWorkflowStatus());
			// Induce change detection by slicing array
			this.workflowStatuses = this.workflowStatuses.slice();
		}

		this.filterWorkflowStatuses();
	}

	/**
	 * Initiates an EventSource for action statuses from the server. Binds various events to the event handler.
	 */
	getActionStatusSSE(): void {
		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				const eventSource = new (window as any).EventSource(`api/streams/workflowqueue/actions?access_token=${authToken}`);

				eventSource.addEventListener('started', (e: any) => this.actionStatusEventHandler(e));
				eventSource.addEventListener('success', (e: any) => this.actionStatusEventHandler(e));
				eventSource.addEventListener('failure', (e: any) => this.actionStatusEventHandler(e));

				eventSource.onerror = (err: Error) => {
					console.error(err);
				};
			});
	}

	/**
	 * Handles an EventSource message for Action Status. 
	 * Updates the parent workflow status' current_action if applicable.
	 * Will add/update action statuses for display if the parent workflow execution is 'loaded' in the modal.
	 * @param message EventSource message for action status
	 */
	actionStatusEventHandler(message: any): void {
		const actionStatusEvent: ActionStatusEvent = JSON.parse(message.data);

		// if we have a matching workflow status, update the current app/action info.
		const matchingWorkflowStatus = this.workflowStatuses
			.find(ws => ws.execution_id === actionStatusEvent.workflow_execution_id);

		if (matchingWorkflowStatus) {
			matchingWorkflowStatus.current_action = {
				execution_id: actionStatusEvent.execution_id,
				id: actionStatusEvent.action_id,
				name: actionStatusEvent.name,
				app_name: actionStatusEvent.app_name,
				action_name: actionStatusEvent.action_name,
			};
		}

		// also add this to the modal if possible, or update the existing data.
		if (this.loadedWorkflowStatus && this.loadedWorkflowStatus.execution_id === actionStatusEvent.workflow_execution_id) {
			const matchingActionStatus = this.loadedWorkflowStatus.action_statuses
				.find(r => r.execution_id === actionStatusEvent.execution_id);

			if (matchingActionStatus) {
				switch (message.type) {
					case 'started':
						matchingActionStatus.started_at = actionStatusEvent.timestamp;
						break;
					case 'success':
					case 'failure':
						matchingActionStatus.completed_at = actionStatusEvent.timestamp;
						break;
					default:
						this.toastyService.warning(`Unknown Action Status SSE Type: ${message.type}.`);
						break;
				}
			} else {
				this.loadedWorkflowStatus.action_statuses.push(actionStatusEvent.toNewActionStatus());
				// Induce change detection by slicing array
				this.loadedWorkflowStatus.action_statuses = this.loadedWorkflowStatus.action_statuses.slice();
			}
		}

		this.filterWorkflowStatuses();
	}

	/**
	 * Calls the workflow status endpoint to command a non-finished workflow to perform some action.
	 * @param workflowStatus WorkflowStatus to perform the action
	 * @param actionName Name of action to take (e.g. pause, resume, abort)
	 */
	performWorkflowStatusAction(workflowStatus: WorkflowStatus, actionName: string): void {
		this.executionService
			.performWorkflowStatusAction(workflowStatus.execution_id, actionName)
			.then(() => this.toastyService.success(`Successfully told ${workflowStatus.name} to  ${actionName}`))
			.catch(e => this.toastyService.error(`Error performing ${actionName} on workflow: ${e.message}`));
	}

	/**
	 * Gets a list of playbooks and workflows from the server and compiles them into a list for selection.
	 */
	getWorkflows(): void {
		this.executionService
			.getPlaybooks()
			.then(playbooks => {
				// Map all of the playbook's workflows and collapse them into a single top-level array.
				this.workflows = playbooks
					.map(pb => pb.workflows)
					.reduce((a, b) => a.concat(b), []);

				const workflowSelectData: Select2OptionData[] = [{ id: '', text: '' }];

				playbooks.forEach(playbook => {
					playbook.workflows.forEach(workflow => {
						workflowSelectData.push({
							id: workflow.id,
							text: `${playbook.name} - ${workflow.name}`,
						});
					});
				});

				this.availableWorkflows = workflowSelectData;
			});
	}

	/**
	 * Executes a given workflow. Uses the selected workflow (specified via the select2 box).
	 */
	excuteSelectedWorkflow(): void {
		this.executionService.addWorkflowToQueue(this.selectedWorkflow.id)
			.then(() => {
				this.toastyService.success(`Successfully started execution of "${this.selectedWorkflow.name}"`);
			})
			.catch(e => this.toastyService.error(`Error executing workflow: ${e.message}`));
	}

	/**
	 * Specifies the selected workflow from the select2. Used because in at least the version of select2 component we have,
	 * There is no two-way data binding available.
	 * @param event Event fired from the workflow select2 change.
	 */
	workflowSelectChange(event: any): void {
		if (!event.value || event.value === '') {
			this.selectedWorkflow = null;
		} else {
			this.selectedWorkflow = this.workflows.find(w => w.id === event.value);
		}
	}

	/**
	 * Opens a modal that contains the action results for a given workflow status.
	 * @param event JS Event from the hyperlink click
	 * @param workflowStatus Workflow Status to get action results for
	 */
	openActionStatusModal(event: Event, workflowStatus: WorkflowStatus): void {
		event.preventDefault();

		let actionResultsPromise: Promise<void>;
		if (this.loadedWorkflowStatus && this.loadedWorkflowStatus.execution_id === workflowStatus.execution_id) {
			actionResultsPromise = Promise.resolve();
		} else {
			actionResultsPromise = this.executionService.getWorkflowStatus(workflowStatus.execution_id)
				.then(fullWorkflowStatus => {
					this.loadedWorkflowStatus = fullWorkflowStatus;
				})
				.catch(e => this.toastyService
					.error(`Error loading action results for "${workflowStatus.name}": ${e.message}`));
		}

		actionResultsPromise.then(() => {
			($('.actionStatusModal') as any).modal('show');
		});
	}

	/**
	 * Converts an input object/value to a friendly string for display in the workflow status table.
	 * @param input Input object / value to convert
	 */
	getFriendlyJSON(input: any): string {
		if (!input) { return 'N/A'; }
		let out = JSON.stringify(input, null, 1);
		out = out.replace(/[\{\[\}\]"]/g, '').trim();
		if (!out) { return 'N/A'; }
		return out;
	}

	/**
	 * Converts an input argument array to a friendly string for display in the workflow status table.
	 * @param args Array of arguments to convert
	 */
	getFriendlyArguments(args: Argument[]): string {
		if (!args || !args.length) { return 'N/A'; }

		const obj: { [key: string]: string } = {};
		args.forEach(element => {
			if (element.value) { obj[element.name] = element.value; }
			if (element.reference) { obj[element.name] = element.reference.toString(); }
			if (element.selection && element.selection.length) {
				const selectionString = (element.selection as any[]).join('.');
				obj[element.name] = `${obj[element.name]} (${selectionString})`;
			}
		});

		let out = JSON.stringify(obj, null, 1);
		out = out.replace(/[\{\}"]/g, '');
		return out;
	}

	/**
	 * Gets the app name from a current action object or returns N/A if undefined.
	 * @param currentAction CurrentAction to use as input
	 */
	getAppName(currentAction: CurrentAction): string {
		if (!currentAction) { return'N/A'; }
		return currentAction.app_name;
	}

	/**
	 * Gets the action name from a current action object or returns N/A if undefined.
	 * @param currentAction CurrentAction to use as input
	 */
	getActionName(currentAction: CurrentAction): string {
		if (!currentAction) { return'N/A'; }
		let output = currentAction.name;
		if (output !== currentAction.action_name) { output = `${output} (${currentAction.action_name})`; }
		return output;
	}

	/**
	 * Simple comparator function for the datatable sort on the app name column.
	 * @param propA Left side CurrentAction
	 * @param propB Right side CurrentAction
	 */
	appNameComparator(propA: CurrentAction, propB: CurrentAction) {
		if (!propA) { return 1; }
		if (!propB) { return -1; }
		
		if (propA.app_name.toLowerCase() < propB.app_name.toLowerCase()) { return -1; }
		if (propA.app_name.toLowerCase() > propB.app_name.toLowerCase()) { return 1; }
	}

	/**
	 * Simple comparator function for the datatable sort on the action name column.
	 * @param propA Left side CurrentAction
	 * @param propB Right side CurrentAction
	 */
	actionNameComparator(propA: CurrentAction, propB: CurrentAction) {
		if (!propA) { return 1; }
		if (!propB) { return -1; }
		
		if (propA.action_name.toLowerCase() < propB.action_name.toLowerCase()) { return -1; }
		if (propA.action_name.toLowerCase() > propB.action_name.toLowerCase()) { return 1; }
	}
}
