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
import { Workflow } from '../models/playbook/workflow';
import { Argument } from '../models/playbook/argument';
import { GenericObject } from '../models/genericObject';
import { NodeStatus, NodeStatuses } from '../models/execution/nodeStatus';

import { ExecutionVariableModalComponent } from './execution.variable.modal.component';
import { EnvironmentVariable } from '../models/playbook/environmentVariable';
import { Router } from '@angular/router';
import * as moment from 'moment';
import { ResultsModalComponent } from './results.modal.component';

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
	@ViewChild('nodeStatusContainer', { static: false }) nodeStatusContainer: ElementRef;
	@ViewChild('nodeStatusTable', { static: false }) nodeStatusTable: DatatableComponent;
	@ViewChild('workflowStatusTable', { static: false }) workflowStatusTable: DatatableComponent;

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

	filterQuery: FormControl = new FormControl();

	workflowStatusEventSource: any;
	nodeStatusEventSource: any;
	recalculateTableCallback: any;
	NodeStatuses = NodeStatuses;

	workflowStatusSocket: SocketIOClient.Socket;
	nodeStatusSocket: SocketIOClient.Socket;

	constructor(
		private executionService: ExecutionService, private authService: AuthService, private cdr: ChangeDetectorRef,
		private toastrService: ToastrService, private utils: UtilitiesService,
		private modalService: NgbModal, private router: Router
	) {}

	/**
	 * On component init, set up our workflow select2 config.
	 * Also get workflows to select, workflow statuses to display in the datatable.
	 * Set up sockets for workflow status and action status to add/update data in our datatables.
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
		this.createNodeStatusSocket();
		this.createWorkflowStatusSocket();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterWorkflowStatuses());

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
	 * Closes our sockets on component destroy.
	 */
	ngOnDestroy(): void {
		if (this.workflowStatusSocket && this.workflowStatusSocket.close) {
			this.workflowStatusSocket.close();
		}
		if (this.nodeStatusSocket && this.nodeStatusSocket.close) {
			this.nodeStatusSocket.close();
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

		// Induce change detection by slicing array
		this.workflowStatuses = this.workflowStatuses.slice();

		this.displayWorkflowStatuses = this.workflowStatuses.filter((s) => {
			return [ 
				s.workflow_id, s.execution_id, s.name, s.status, s.action_name, s.app_name, s.label
			].some(x => x && x.toLocaleLowerCase().includes(searchFilter));
		});

		this.workflowStatusTable.recalculate();
	}

	/**
	 * Gets a list of workflow statuses from the server for initial population.
	 */
	getWorkflowStatuses(): void {
		this.executionService
			.getAllWorkflowStatuses()
			.then(workflowStatuses => this.displayWorkflowStatuses = this.workflowStatuses = workflowStatuses)
			.catch(e => this.toastrService.error(`Error retrieving workflow statuses: ${e.message}`));
	}

	/**
	 * Initiates an Socket for workflow statuses from the server. Binds various events to the event handler.
	 */
	createWorkflowStatusSocket() {
		if (this.workflowStatusSocket) this.workflowStatusSocket.close();
		this.workflowStatusSocket = this.utils.createSocket('/workflowStatus');

		this.workflowStatusSocket.on('connected', (data: any[]) => {
			const events = plainToClass(WorkflowStatus, data);
			events.forEach(event => this.workflowStatusEventHandler(event));
		});

		this.workflowStatusSocket.on('log', (data: any) => {
			const event = plainToClass(WorkflowStatus, data);
			console.log(event);
			this.workflowStatusEventHandler(event)
		});
	}

	/**
	 * Handles an Socket message for Workflow Status.
	 * Updates existing workflow statuses for status updates or adds new ones to the list for display.
	 * @param message Socket message for workflow status
	 */
	workflowStatusEventHandler(workflowStatus: WorkflowStatus): void {
		const matchingWorkflowStatus = this.workflowStatuses.find(ws => ws.execution_id === workflowStatus.execution_id);

		if (matchingWorkflowStatus) {
			matchingWorkflowStatus.status = workflowStatus.status;
			matchingWorkflowStatus.node_statuses = workflowStatus.node_statuses;

			switch (workflowStatus.status) {
				case WorkflowStatuses.PENDING:
					break;
				case WorkflowStatuses.EXECUTING:
					if (!matchingWorkflowStatus.started_at) {
						matchingWorkflowStatus.started_at = workflowStatus.started_at;
					}
					matchingWorkflowStatus.user = workflowStatus.user;
					matchingWorkflowStatus.app_name = workflowStatus.app_name;
					matchingWorkflowStatus.action_name = workflowStatus.action_name;
					matchingWorkflowStatus.label = workflowStatus.label;
					break;
				case WorkflowStatuses.PAUSED:
				case WorkflowStatuses.AWAITING_DATA:
					break;
				case WorkflowStatuses.COMPLETED:
					matchingWorkflowStatus.completed_at = workflowStatus.completed_at;
					break;
				case WorkflowStatuses.ABORTED:
					matchingWorkflowStatus.completed_at = workflowStatus.completed_at;
					break;
				default:
					this.toastrService.warning(`Unknown Workflow Status Type: ${workflowStatus.status}.`);
					break;
			}
		} else {
			this.workflowStatuses.push(workflowStatus);
		}

		this.filterWorkflowStatuses();
	}

	/**
	 * Initiates an Socket for action statuses from the server. Binds various events to the event handler.
	 */
	createNodeStatusSocket() {
		if (this.nodeStatusSocket) this.nodeStatusSocket.close();
		this.nodeStatusSocket = this.utils.createSocket('/nodeStatus');

		this.nodeStatusSocket.on('connected', (data: any[]) => {
			const events = plainToClass(NodeStatus, data);
			events.forEach(event => this.nodeStatusEventHandler(event));
		});

		this.nodeStatusSocket.on('log', (data: any) => {
			const event = plainToClass(NodeStatus, data);
			console.log(event);
			this.nodeStatusEventHandler(event)
		});
	}

	/**
	 * Handles an Socket message for Action Status.
	 * Updates the parent workflow status' current_node if applicable.
	 * Will add/update action statuses for display if the parent workflow execution is 'loaded' in the modal.
	 * @param message Socket message for action status
	 */
	nodeStatusEventHandler(nodeStatus: NodeStatus): void {
		// add this to the modal if possible, or update the existing data.
		if (this.loadedWorkflowStatus && this.loadedWorkflowStatus.execution_id === nodeStatus.execution_id) {
			const matchingNodeStatus = this.loadedWorkflowStatus.node_statuses
				.find(r => r.combined_id === nodeStatus.combined_id);

			if (matchingNodeStatus) {
				matchingNodeStatus.status = nodeStatus.status;

				switch (nodeStatus.status) {
					case NodeStatuses.EXECUTING:
						matchingNodeStatus.started_at = nodeStatus.started_at;
						break;
					case NodeStatuses.SUCCESS:
					case NodeStatuses.FAILURE:
						matchingNodeStatus.completed_at = nodeStatus.completed_at;
						matchingNodeStatus.result = nodeStatus.result;
						break;
					case NodeStatuses.AWAITING_DATA:
						// don't think anything needs to happen here
						break;
					default:
						this.toastrService.warning(`Unknown Action Status Type: ${ nodeStatus.status }.`);
						break;
				}
			} else {
				this.loadedWorkflowStatus.node_statuses.push(nodeStatus);
				// Induce change detection by slicing array
				this.loadedWorkflowStatus.node_statuses = this.loadedWorkflowStatus.node_statuses.slice();
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

		let nodeResultsPromise: Promise<any>;
		if (this.loadedWorkflowStatus && this.loadedWorkflowStatus.execution_id === workflowStatus.execution_id) {
			nodeResultsPromise = Promise.resolve();
		} else {
			nodeResultsPromise = this.executionService.getWorkflowStatus(workflowStatus.execution_id)
				.then(fullWorkflowStatus => this.loadedWorkflowStatus = fullWorkflowStatus)
				.catch(e => {
					this.toastrService.error(`Error loading action results for "${workflowStatus.name}": ${e.message}`)
				});
		}

		nodeResultsPromise.then(() => {
			//($('.nodeStatusModal') as any).modal('show');
			const modalRef = this.modalService.open(ResultsModalComponent, { windowClass: 'modal-xxl', centered: true });
			modalRef.componentInstance.loadedWorkflowStatus = this.loadedWorkflowStatus;
		});
	}

	/**
	 * Simple comparator function for the datatable sort on a date column.
	 * @param propA Left side date
	 * @param propB Right side date
	 */
	dateComparator(propA, propB) {
		if (!propA && !propB) return 0;
		if (!propA) return 1;
		if (!propB) return -1;
		return moment(propA).diff(moment(propB));
	}

	getClipboard(results) {
        return  $.isPlainObject(results) ? JSON.stringify(results, null, 2) : results;
    }
}
