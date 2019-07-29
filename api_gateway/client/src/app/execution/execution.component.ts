import { Component, ViewEncapsulation, OnInit, AfterViewChecked, ElementRef, ViewChild,
	ChangeDetectorRef, OnDestroy } from '@angular/core';
import { FormControl } from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { Select2OptionData } from 'ng2-select2';
import { DatatableComponent } from '@swimlane/ngx-datatable';
import { interval } from 'rxjs';
import 'rxjs/add/operator/debounceTime';
import { plainToClass } from 'class-transformer';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';

import { ExecutionService } from './execution.service';
import { AuthService } from '../auth/auth.service';
import { UtilitiesService } from '../utilities.service';

import { WorkflowStatus, WorkflowStatuses } from '../models/execution/workflowStatus';
import { WorkflowStatusEvent } from '../models/execution/workflowStatusEvent';
import { Workflow } from '../models/playbook/workflow';
import { NodeStatusEvent } from '../models/execution/nodeStatusEvent';
import { Argument } from '../models/playbook/argument';
import { GenericObject } from '../models/genericObject';
import { NodeStatus, NodeStatuses } from '../models/execution/nodeStatus';

import { ExecutionVariableModalComponent } from './execution.variable.modal.component';
import { EnvironmentVariable } from '../models/playbook/environmentVariable';
import { NodeStatusSummary } from '../models/execution/nodeStatusSummary';
import { Router } from '@angular/router';
import * as moment from 'moment';

@Component({
	selector: 'execution-component',
	templateUrl: './execution.html',
	styleUrls: [
		'./execution.scss',
	],
	encapsulation: ViewEncapsulation.None,
	providers: [AuthService],
})
export class ExecutionComponent implements OnInit, AfterViewChecked, OnDestroy {
	@ViewChild('nodeStatusContainer') nodeStatusContainer: ElementRef;
	@ViewChild('nodeStatusTable') nodeStatusTable: DatatableComponent;

	schedulerStatus: string;
	workflowStatuses: WorkflowStatus[] = [];
	displayWorkflowStatuses: WorkflowStatus[] = [];
	workflows: Workflow[] = [];
	availableWorkflows: Select2OptionData[] = [];
	workflowSelectConfig: Select2Options;
	selectedWorkflow: Workflow;
	loadedWorkflowStatus: WorkflowStatus;
	nodeStatusComponentWidth: number;
	workflowStatusActions: GenericObject;
	workflowStatusStartedRelativeTimes: { [key: string]: string } = {};
	workflowStatusCompletedRelativeTimes: { [key: string]: string } = {};
	nodeStatusStartedRelativeTimes: { [key: string]: string } = {};
	nodeStatusCompletedRelativeTimes: { [key: string]: string } = {};

	filterQuery: FormControl = new FormControl();

	workflowStatusEventSource: any;
	nodeStatusEventSource: any;
	recalculateTableCallback: any;

	constructor(
		private executionService: ExecutionService, private authService: AuthService, private cdr: ChangeDetectorRef,
		private toastrService: ToastrService, private utils: UtilitiesService,
		private modalService: NgbModal, private router: Router
	) {}

	/**
	 * On component init, set up our workflow select2 config.
	 * Also get workflows to select, workflow statuses to display in the datatable.
	 * Set up SSEs for workflow status and action status to add/update data in our datatables.
	 */
	ngOnInit(): void {

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
		this.getNodeStatusSSE();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterWorkflowStatuses());

		interval(30000).subscribe(() => {
			this.recalculateRelativeTimes();
		});

		this.recalculateTableCallback = (e: any) => {
			if (this.nodeStatusTable && this.nodeStatusTable.recalculate) {
				if (Array.isArray(this.nodeStatusTable.rows))
					this.nodeStatusTable.rows = [...this.nodeStatusTable.rows];
				this.nodeStatusTable.recalculate();
			}
		}

		$(document).on('shown.bs.modal', '.nodeStatusModal', this.recalculateTableCallback)
	}

	/**
	 * This angular function is used primarily to recalculate column widths for execution results table.
	 */
	ngAfterViewChecked(): void {
		// Check if the table size has changed, and recalculate.
		if (this.nodeStatusTable && this.nodeStatusTable.recalculate &&
			(this.nodeStatusContainer.nativeElement.clientWidth !== this.nodeStatusComponentWidth)) {
			this.nodeStatusComponentWidth = this.nodeStatusContainer.nativeElement.clientWidth;
			this.nodeStatusTable.recalculate();
			this.cdr.detectChanges();
		}
	}

	/**
	 * Closes our SSEs on component destroy.
	 */
	ngOnDestroy(): void {
		if (this.workflowStatusEventSource && this.workflowStatusEventSource.close) {
			this.workflowStatusEventSource.close();
		}
		if (this.nodeStatusEventSource && this.nodeStatusEventSource.close) {
			this.nodeStatusEventSource.close();
		}
		if (this.recalculateTableCallback) {
			$(document).off('shown.bs.modal', '.nodeStatusModal', this.recalculateTableCallback)
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
				(s.node_status &&
					(s.node_status.name.toLocaleLowerCase().includes(searchFilter) ||
					s.node_status.label.toLocaleLowerCase().includes(searchFilter) ||
					s.node_status.app_name.toLocaleLowerCase().includes(searchFilter)));
		});
	}

	/**
	 * Gets a list of workflow statuses from the server for initial population.
	 */
	getWorkflowStatuses(): void {
		this.executionService
			.getAllWorkflowStatuses()
			.then(workflowStatuses => {
				workflowStatuses.forEach(workflowStatus => {
					this.calculateLocalizedTimes(workflowStatus);
				});
				this.displayWorkflowStatuses = this.workflowStatuses = workflowStatuses;
				this.recalculateRelativeTimes();
			})
			.catch(e => this.toastrService.error(`Error retrieving workflow statuses: ${e.message}`));
	}

	/**
	 * Initiates an EventSource for workflow statuses from the server. Binds various events to the event handler.
	 */
	getWorkflowStatusSSE(): void {
		this.authService.getEventSource('/api/streams/workflowqueue/workflow_status')
			.then(eventSource => {
				this.workflowStatusEventSource = eventSource;
				this.workflowStatusEventSource.onerror = (e: any) => this.statusEventErrorHandler(e);
				Object.values(WorkflowStatuses)
					  .forEach(status => this.workflowStatusEventSource.addEventListener(status, (e: any) => this.workflowStatusEventHandler(e)));
			});
	}

	/**
	 * Handles an EventSource message for Workflow Status.
	 * Updates existing workflow statuses for status updates or adds new ones to the list for display.
	 * @param message EventSource message for workflow status
	 */
	workflowStatusEventHandler(message: any): void {
		const workflowStatusEvent = plainToClass(WorkflowStatusEvent, (JSON.parse(message.data) as object));
		console.log(workflowStatusEvent);

		const matchingWorkflowStatus = this.workflowStatuses.find(ws => ws.execution_id === workflowStatusEvent.execution_id);

		if (matchingWorkflowStatus) {
			matchingWorkflowStatus.status = workflowStatusEvent.status;

			switch (message.type) {
				case WorkflowStatuses.PENDING:
					delete matchingWorkflowStatus.node_status;
					break;
				case WorkflowStatuses.EXECUTING:
					if (!matchingWorkflowStatus.started_at) {
						matchingWorkflowStatus.started_at = workflowStatusEvent.started_at;
						this.workflowStatusStartedRelativeTimes[matchingWorkflowStatus.execution_id] =
							this.utils.getRelativeLocalTime(workflowStatusEvent.started_at);
					}
					matchingWorkflowStatus.user = workflowStatusEvent.user;
					matchingWorkflowStatus.node_status = workflowStatusEvent.node_status;
					break;
				case WorkflowStatuses.PAUSED:
				case WorkflowStatuses.AWAITING_DATA:
				//case 'resumed':
				//case 'triggered':
					matchingWorkflowStatus.node_status = workflowStatusEvent.node_status;
					break;
				case WorkflowStatuses.COMPLETED:
					// Add a delay to ensure completed status is updated in quick executing workflows
					setTimeout(() => {
						matchingWorkflowStatus.completed_at = workflowStatusEvent.completed_at;
						this.workflowStatusCompletedRelativeTimes[matchingWorkflowStatus.execution_id] =
							this.utils.getRelativeLocalTime(workflowStatusEvent.completed_at);
						delete matchingWorkflowStatus.node_status;
					}, 250);
					break;
				case WorkflowStatuses.ABORTED:
					matchingWorkflowStatus.completed_at = workflowStatusEvent.completed_at;
					this.workflowStatusCompletedRelativeTimes[matchingWorkflowStatus.execution_id] =
						this.utils.getRelativeLocalTime(workflowStatusEvent.completed_at);
					break;
				default:
					this.toastrService.warning(`Unknown Workflow Status SSE Type: ${message.type}.`);
					break;
			}

			this.calculateLocalizedTimes(matchingWorkflowStatus);
		} else {
			const newWorkflowStatus = workflowStatusEvent.toNewWorkflowStatus();
			this.calculateLocalizedTimes(newWorkflowStatus);
			this.workflowStatuses.push(newWorkflowStatus);
			// Induce change detection by slicing array
			this.workflowStatuses = this.workflowStatuses.slice();
		}

		this.filterWorkflowStatuses();
	}

	/**
	 * Initiates an EventSource for action statuses from the server. Binds various events to the event handler.
	 */
	getNodeStatusSSE(workflowExecutionId: string = null): void {
		if (this.nodeStatusEventSource) this.nodeStatusEventSource.close();

		let url = `/api/streams/workflowqueue/actions?summary=true`;
		if (workflowExecutionId) url += `&workflow_execution_id=${ workflowExecutionId }`;

		this.authService.getEventSource(url)
			.then(eventSource => {
				this.nodeStatusEventSource = eventSource;
				this.nodeStatusEventSource.onerror = (e: any) => this.statusEventErrorHandler(e);

				Object.values(NodeStatuses)
					  .forEach(status => this.nodeStatusEventSource.addEventListener(status, (e: any) => this.nodeStatusEventHandler(e)));
			});
	}

	/**
	 * Handles an EventSource message for Action Status.
	 * Updates the parent workflow status' current_node if applicable.
	 * Will add/update action statuses for display if the parent workflow execution is 'loaded' in the modal.
	 * @param message EventSource message for action status
	 */
	nodeStatusEventHandler(message: any): void {
		const nodeStatusEvent = plainToClass(NodeStatusEvent, (JSON.parse(message.data) as object));
		console.log(nodeStatusEvent);

		// if we have a matching workflow status, update the current app/action info.
		const matchingWorkflowStatus = this.workflowStatuses
			.find(ws => ws.execution_id === nodeStatusEvent.execution_id);

		if (matchingWorkflowStatus) {
			matchingWorkflowStatus.node_status = plainToClass(NodeStatusSummary, {
				execution_id: nodeStatusEvent.execution_id,
				id: nodeStatusEvent.node_id,
				name: nodeStatusEvent.name,
				app_name: nodeStatusEvent.app_name,
				label: nodeStatusEvent.label,
			});
		}

		// also add this to the modal if possible, or update the existing data.
		if (this.loadedWorkflowStatus && this.loadedWorkflowStatus.execution_id === nodeStatusEvent.execution_id) {
			const matchingNodeStatus = this.loadedWorkflowStatus.node_statuses
				.find(r => r.execution_id === nodeStatusEvent.execution_id);

			if (matchingNodeStatus) {
				matchingNodeStatus.status = nodeStatusEvent.status;

				switch (message.type) {
					case NodeStatuses.EXECUTING:
						matchingNodeStatus.started_at = nodeStatusEvent.started_at;
						this.nodeStatusStartedRelativeTimes[matchingNodeStatus.execution_id] =
							this.utils.getRelativeLocalTime(nodeStatusEvent.started_at);
						break;
					case NodeStatuses.SUCCESS:
					case NodeStatuses.FAILURE:
						matchingNodeStatus.completed_at = nodeStatusEvent.completed_at;
						matchingNodeStatus.result = nodeStatusEvent.result;
						this.nodeStatusCompletedRelativeTimes[matchingNodeStatus.execution_id] =
							this.utils.getRelativeLocalTime(nodeStatusEvent.completed_at);
						break;
					case NodeStatuses.AWAITING_DATA:
						// don't think anything needs to happen here
						break;
					default:
						this.toastrService.warning(`Unknown Action Status SSE Type: ${message.type}.`);
						break;
				}

				this.calculateLocalizedTimes(matchingNodeStatus);
			} else {
				const newNodeStatus = nodeStatusEvent.toNewNodeStatus();
				this.calculateLocalizedTimes(newNodeStatus);
				this.loadedWorkflowStatus.node_statuses.push(newNodeStatus);
				// Induce change detection by slicing array
				this.loadedWorkflowStatus.node_statuses = this.loadedWorkflowStatus.node_statuses.slice();
			}
		}

		this.filterWorkflowStatuses();
	}

	statusEventErrorHandler(e: any) {
		if (this.nodeStatusEventSource && this.nodeStatusEventSource.close)
			this.nodeStatusEventSource.close();
		if (this.workflowStatusEventSource && this.workflowStatusEventSource.close)
			this.workflowStatusEventSource.close();

		const options = {backdrop: undefined, closeButton: false, buttons: { ok: { label: 'Reload Page' }}}
		this.utils
			.alert('The server stopped responding. Reload the page to try again.', options)
			.then(() => location.reload(true))
	}

	/**
	 * Calls the workflow status endpoint to command a non-finished workflow to perform some action.
	 * @param workflowStatus WorkflowStatus to perform the action
	 * @param actionName Name of action to take (e.g. pause, resume, abort)
	 */
	performWorkflowStatusAction(workflowStatus: WorkflowStatus, actionName: string): void {
		this.executionService
			.performWorkflowStatusAction(workflowStatus.execution_id, actionName)
			.then(() => this.toastrService.success(`Successfully told ${workflowStatus.name} to  ${actionName}`))
			.catch(e => this.toastrService.error(`Error performing ${actionName} on workflow: ${e.message}`));
	}

	/**
	 * Gets a list of playbooks and workflows from the server and compiles them into a list for selection.
	 */
	getWorkflows(): void {
		this.executionService
			.getWorkflows()
			.then(workflows => {
				// Map all of the playbook's workflows and collapse them into a single top-level array.
				this.workflows = workflows

				const workflowSelectData: Select2OptionData[] = [{ id: '', text: '' }];

				workflows.forEach(workflow => {
					workflowSelectData.push({
						id: workflow.id,
						text: `${workflow.name}`,
					});
				});

				this.availableWorkflows = workflowSelectData;
			});
	}

	/**
	 * Executes a given workflow. Uses the selected workflow (specified via the select2 box).
	 */
	executeSelectedWorkflow(environmentVariables: EnvironmentVariable[] = []): void {
		this.executionService.addWorkflowToQueue(this.selectedWorkflow.id, null, environmentVariables)
			.then((workflowStatus: WorkflowStatus) => {
				this.toastrService.success(`Starting <b>${this.selectedWorkflow.name}</b>`);
			})
			.catch(e => this.toastrService.error(`Error executing workflow: ${e.message}`));
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
			this.executionService.loadWorkflow(this.selectedWorkflow.id).then(workflow => {
				if (this.selectedWorkflow.id == workflow.id) this.selectedWorkflow = workflow;
			})
		}
	}

	openVariableModal() {
		const modalRef = this.modalService.open(ExecutionVariableModalComponent);
		modalRef.componentInstance.workflow = this.selectedWorkflow;
		modalRef.result.then(variables => {
			this.executeSelectedWorkflow(variables);
		}).catch(() => null)
	}

	/**
	 * Opens a modal that contains the action results for a given workflow status.
	 * @param event JS Event from the hyperlink click
	 * @param workflowStatus Workflow Status to get action results for
	 */
	openNodeStatusModal(event: Event, workflowStatus: WorkflowStatus): void {
		event.preventDefault();

		let nodeResultsPromise: Promise<void>;
		if (this.loadedWorkflowStatus && this.loadedWorkflowStatus.execution_id === workflowStatus.execution_id) {
			nodeResultsPromise = Promise.resolve();
		} else {
			nodeResultsPromise = this.executionService.getWorkflowStatus(workflowStatus.execution_id)
				.then(fullWorkflowStatus => {
					this.calculateLocalizedTimes(fullWorkflowStatus);
					fullWorkflowStatus.node_statuses.forEach(nodeStatus => {
						this.calculateLocalizedTimes(nodeStatus);
					});
					this.loadedWorkflowStatus = fullWorkflowStatus;
					this.recalculateRelativeTimes();

				})
				.catch(e => {
					this.toastrService.error(`Error loading action results for "${workflowStatus.name}": ${e.message}`)
				});
		}

		nodeResultsPromise.then(() => {
			($('.nodeStatusModal') as any).modal('show');
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
		});

		let out = JSON.stringify(obj, null, 1);
		out = out.replace(/[\{\}"]/g, '');
		return out;
	}

	/**
	 * Gets the app name from a current node object or returns N/A if undefined.
	 * @param nodeStatusSummary NodeStatusSummary to use as input
	 */
	getAppName(nodeStatusSummary: NodeStatusSummary): string {
		if (!nodeStatusSummary) { return'N/A'; }
		return nodeStatusSummary.app_name;
	}

	/**
	 * Gets the action name from a current node object or returns N/A if undefined.
	 * @param nodeStatusSummary NodeStatusSummary to use as input
	 */
	getActionName(nodeStatusSummary: NodeStatusSummary): string {
		if (!nodeStatusSummary) { return'N/A'; }
		let output = nodeStatusSummary.label;
		if (output !== nodeStatusSummary.name) { output = `${output} (${nodeStatusSummary.name})`; }
		return output;
	}

	/**
	 * Simple comparator function for the datatable sort on the app name column.
	 * @param propA Left side NodeStatusSummary
	 * @param propB Right side NodeStatusSummary
	 */
	appNameComparator(propA: NodeStatusSummary, propB: NodeStatusSummary) {
		if (!propA) { return 1; }
		if (!propB) { return -1; }

		if (propA.app_name.toLowerCase() < propB.app_name.toLowerCase()) { return -1; }
		if (propA.app_name.toLowerCase() > propB.app_name.toLowerCase()) { return 1; }
	}

	/**
	 * Simple comparator function for the datatable sort on a date column.
	 * @param propA Left side NodeStatusSummary
	 * @param propB Right side NodeStatusSummary
	 */
	dateComparator(propA, propB) {
		if (!propA && !propB) return 0;
		if (!propA) return 1; 
		if (!propB) return -1;
		return moment(propA).diff(moment(propB));
	}

	/**
	 * Simple comparator function for the datatable sort on the action name column.
	 * @param propA Left side NodeStatusSummary
	 * @param propB Right side NodeStatusSummary
	 */
	actionNameComparator(propA: NodeStatusSummary, propB: NodeStatusSummary) {
		if (!propA) { return 1; }
		if (!propB) { return -1; }

		if (propA.name.toLowerCase() < propB.name.toLowerCase()) { return -1; }
		if (propA.name.toLowerCase() > propB.name.toLowerCase()) { return 1; }
	}

	/**
	 * Recalculates the relative times shown for start/end date timestamps (e.g. '5 hours ago').
	 */
	recalculateRelativeTimes(): void {
		if (!this.workflowStatuses || !this.workflowStatuses.length) { return; }

		this.workflowStatuses.forEach(workflowStatus => {
			if (workflowStatus.started_at) {
				this.workflowStatusStartedRelativeTimes[workflowStatus.execution_id] =
					this.utils.getRelativeLocalTime(workflowStatus.started_at);
			}
			if (workflowStatus.completed_at) {
				this.workflowStatusCompletedRelativeTimes[workflowStatus.execution_id] =
					this.utils.getRelativeLocalTime(workflowStatus.completed_at);
			}
		});

		if (!this.loadedWorkflowStatus || !this.loadedWorkflowStatus.node_statuses ||
			!this.loadedWorkflowStatus.node_statuses.length ) { return; }

		this.loadedWorkflowStatus.node_statuses.forEach(nodeStatus => {
			if (nodeStatus.started_at) {
				this.nodeStatusStartedRelativeTimes[nodeStatus.execution_id] =
					this.utils.getRelativeLocalTime(nodeStatus.started_at);
			}
			if (nodeStatus.completed_at) {
				this.nodeStatusCompletedRelativeTimes[nodeStatus.execution_id] =
					this.utils.getRelativeLocalTime(nodeStatus.completed_at);
			}
		});
	}

	/**
	 * Adds/updates localized time strings to a status object.
	 * @param status Workflow or Action Status to mutate
	 */
	calculateLocalizedTimes(status: WorkflowStatus | NodeStatus): void {
		if (status.started_at) {
			status.localized_started_at = this.utils.getLocalTime(status.started_at);
		}
		if (status.completed_at) {
			status.localized_completed_at = this.utils.getLocalTime(status.completed_at);
		}
	}
}
