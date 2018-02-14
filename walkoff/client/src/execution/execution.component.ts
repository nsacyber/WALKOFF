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
import { Workflow } from '../models/playbook/workflow';
import { ActionStatus } from '../models/execution/actionStatus';
import { Argument } from '../models/playbook/argument';
import { GenericObject } from '../models/genericObject';

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

	currentController: string;
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
		private toastyService: ToastyService, private toastyConfig: ToastyConfig) {
	}

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

		this.getWorkflowStatuses();
		this.getWorkflowStatusSSE();
		this.getActionResultSSE();

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

	filterWorkflowStatuses(): void {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayWorkflowStatuses = this.workflowStatuses.filter((s) => {
			return (s.name.toLocaleLowerCase().includes(searchFilter));
		});
	}

	getWorkflowStatuses(): void {
		this.executionService
			.getWorkflowStatusList()
			.then(workflowStatuses => this.displayWorkflowStatuses = this.workflowStatuses = workflowStatuses)
			.catch(e => this.toastyService.error(`Error retrieving workflow statuses: ${e.message}`));
	}

	getWorkflowStatusSSE(): void {
		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				const self = this;
				const eventSource = new (window as any)
					.EventSource(`api/streams/workflowqueue/workflow_status?access_token=${authToken}`);

				eventSource.onmessage((message: any) => {
					const workflowStatus: WorkflowStatus = JSON.parse(message.data);

					const matchingWorkflowStatus = self.workflowStatuses.find(ws => ws.execution_id === workflowStatus.execution_id);
					if (matchingWorkflowStatus) {
						Object.assign(matchingWorkflowStatus, workflowStatus);
					} else {
						self.workflowStatuses.push(workflowStatus);
						// Induce change detection by slicing array
						self.workflowStatuses = self.workflowStatuses.slice();
					}

					self.filterWorkflowStatuses();
				});
				eventSource.onerror((err: Error) => {
					console.error(err);
				});
			});
	}

	getActionResultSSE(): void {
		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				const self = this;
				const eventSource = new (window as any).EventSource(`api/streams/workflowqueue/actions?access_token=${authToken}`);

				eventSource.onmessage((message: any) => {
					const actionStatus: ActionStatus = JSON.parse(message.data);

					// if we have a matching workflow status, update the current app/action info.
					const matchingWorkflowStatus = self.workflowStatuses
						.find(ws => ws.execution_id === actionStatus.workflow_execution_id);
					if (matchingWorkflowStatus) {
						matchingWorkflowStatus.current_action_execution_id = actionStatus.execution_id;
						matchingWorkflowStatus.current_action_id = actionStatus.action_id;
						matchingWorkflowStatus.current_app_name = actionStatus.app_name;
						matchingWorkflowStatus.current_action_name = actionStatus.action_name;
					}

					// also add this to the modal if possible
					if (self.loadedWorkflowStatus && self.loadedWorkflowStatus.execution_id === actionStatus.workflow_execution_id) {
						const matchingActionStatus = self.loadedWorkflowStatus.action_statuses
							.find(r => r.execution_id === actionStatus.execution_id);

						if (matchingActionStatus) {
							Object.assign(matchingActionStatus, actionStatus);
						} else {
							self.loadedWorkflowStatus.action_statuses.push(actionStatus);
							// Induce change detection by slicing array
							self.loadedWorkflowStatus.action_statuses = self.loadedWorkflowStatus.action_statuses.slice();
						}
					}

					self.filterWorkflowStatuses();
				});
				eventSource.onerror((err: Error) => {
					console.error(err);
				});
			});
	}

	performWorkflowStatusAction(workflowStatus: WorkflowStatus, actionName: string): void {
		this.executionService
			.performWorkflowStatusAction(workflowStatus.execution_id, actionName)
			.then(updatedWorkflowStatus => {
				Object.assign(workflowStatus, updatedWorkflowStatus);
				
				this.filterWorkflowStatuses();
			})
			.catch(e => this.toastyService.error(`Error performing ${actionName} on workflow: ${e.message}`));
	}

	getWorkflowNames(): void {
		const self = this;

		this.executionService
			.getPlaybooks()
			.then(playbooks => {
				this.workflows = playbooks
					.map(pb => pb.workflows)
					.reduce((a, b) => a.concat(b), []);

				playbooks.forEach(playbook => {
					playbook.workflows.forEach(workflow => {
						self.availableWorkflows.push({
							id: workflow.id,
							text: `${playbook.name} - ${workflow.name}`,
						});
					});
				});
			});
	}

	excuteSelectedWorkflow(): void {
		this.executionService.addWorkflowToQueue(this.selectedWorkflow.id)
			.then(() => {
				this.toastyService.success(`Successfully started execution of "${this.selectedWorkflow.name}"`);
			})
			.catch(e => this.toastyService.error(`Error executing workflow: ${e.message}`));
	}

	workflowSelectChange(event: any): void {
		if (!event.value || event.value === '') {
			this.selectedWorkflow = null;
		} else {
			this.selectedWorkflow = this.workflows.find(w => w.id === event.value);
		}
	}

	openactionStatusModal(workflowStatus: WorkflowStatus): void {
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
			($('#actionResultsModal') as any).modal('show');
		});
	}

	getFriendlyJSON(input: any): string {
		let out = JSON.stringify(input, null, 1);
		out = out.replace(/[\{\[\}\]"]/g, '').trim();
		if (!out) { return 'N/A'; }
		return out;
	}

	getFriendlyArguments(args: Argument[]): string {
		if (!args || !args.length) { return 'N/A'; }

		const obj: { [key: string]: string } = {};
		args.forEach(element => {
			if (element.value) { obj[element.name] = element.value; }
			if (element.reference) { obj[element.name] = element.reference.toString(); }
			if (element.selection) {
				const selectionString = (element.selection as any[]).join('.');
				obj[element.name] = `${obj[element.name]} (${selectionString})`;
			}
		});

		let out = JSON.stringify(obj, null, 1);
		out = out.replace(/[\{\}"]/g, '');
		return out;
	}
}
