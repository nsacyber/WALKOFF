import { Component, ViewEncapsulation } from '@angular/core';
import { FormControl } from '@angular/forms';
import * as _ from 'lodash';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import { Select2OptionData } from 'ng2-select2';
import 'rxjs/add/operator/debounceTime';

import { ExecutionService } from './execution.service';
import { AuthService } from '../auth/auth.service';

import { WorkflowStatus } from '../models/execution/workflowStatus';
import { Workflow } from '../models/playbook/workflow';
import { Playbook } from '../models/playbook/playbook';
import { ActionResult } from '../models/execution/actionResult';

@Component({
	selector: 'scheduler-component',
	templateUrl: './scheduler.html',
	styleUrls: [
		'./scheduler.css',
	],
	encapsulation: ViewEncapsulation.None,
	providers: [ExecutionService, AuthService],
})
export class ExecutionComponent {
	currentController: string;
	schedulerStatus: string;
	workflowStatuses: WorkflowStatus[] = [];
	displayWorkflowStatuses: WorkflowStatus[] = [];
	playbooks: Playbook[] = [];
	workflows: Workflow[] = [];
	availableWorkflows: Select2OptionData[] = [];
	workflowSelectConfig: Select2Options;
	selectedWorkflow: Workflow;

	filterQuery: FormControl = new FormControl();

	constructor(
		private executionService: ExecutionService, private authService: AuthService, private modalService: NgbModal,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig) {
	}

	ngOnInit(): void {
		this.toastyConfig.theme = 'bootstrap';

		this.workflowSelectConfig = {
			width: '100%',
			placeholder: 'Select a Workflow',
		};

		this.getWorkflowStatuses();
		this.getWorkflowStatusSSE();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterWorkflowStatuses());
	}

	filterWorkflowStatuses(): void {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayWorkflowStatuses = this.workflowStatuses.filter((s) => {
			return (s.name.toLocaleLowerCase().includes(searchFilter));
		});
	}

	getWorkflowStatuses(): void {
		this.executionService
			.getWorkflowStatuses()
			.then(workflowStatuses => this.displayWorkflowStatuses = this.workflowStatuses = workflowStatuses)
			.catch(e => this.toastyService.error(`Error retrieving workflow statuses: ${e.message}`));
	}

	getWorkflowStatusSSE(): void {
		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				const self = this;
				const eventSource = new (window as any).EventSource('api/workflowstatus/status-stream?access_token=' + authToken);

				function eventHandler(message: any) {
					const workflowStatus: WorkflowStatus = JSON.parse(message.data);

					const matchingWorkflowStatus = self.workflowStatuses.find(ws => ws.uid === workflowStatus.uid);
					if (matchingWorkflowStatus) {
						Object.assign(matchingWorkflowStatus, workflowStatus);
					} else {
						self.workflowStatuses.push(workflowStatus);
						// Induce change detection by slicing array
						self.workflowStatuses = self.workflowStatuses.slice();
					}

					self.filterWorkflowStatuses();
				}

				eventSource.addEventListener('workflow_status', eventHandler);
				eventSource.addEventListener('error', (err: Error) => {
					// this.toastyService.error(`Error retrieving workflow results: ${err.message}`);
					console.error(err);
				});
			});
	}

	getActionResultSSE(): void {
		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				const self = this;
				const eventSource = new (window as any).EventSource('api/workflowstatus/action-stream?access_token=' + authToken);

				function eventHandler(message: any) {
					const actionResult: ActionResult = JSON.parse(message.data);

					const matchingWorkflowStatus = self.workflowStatuses.find(ws => ws.uid === actionResult.workflow_id);
					if (!matchingWorkflowStatus) { return; }
					matchingWorkflowStatus.current_action_name = `${actionResult.app_name} - ${actionResult.action_name}`;

					// TODO: also add this to the modal if possible

					self.filterWorkflowStatuses();
				}

				eventSource.addEventListener('action_success', eventHandler);
				eventSource.addEventListener('action_error', eventHandler);
				eventSource.addEventListener('error', (err: Error) => {
					// this.toastyService.error(`Error retrieving workflow results: ${err.message}`);
					console.error(err);
				});
			});
	}

	performWorkflowStatusAction(workflowStatus: WorkflowStatus, actionName: string): void {
		const playbook = this._getPlaybookFromWorkflowId(workflowStatus.uid);

		this.executionService
			.performWorkflowStatusAction(playbook.uid, workflowStatus.uid, actionName)
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
				this.playbooks = playbooks;
				this.workflows = playbooks
					.map(pb => pb.workflows)
					.reduce((a, b) => a.concat(b), []);

				playbooks.forEach(function (pb: any) {
					pb.workflows.forEach(function (w: any) {
						self.availableWorkflows.push({
							id: w.uid,
							text: `${pb.name} - ${w.name}`,
						});
					});
				});
			});
	}

	excuteSelectedWorkflow(): void {
		const playbook = this._getPlaybookFromWorkflowId(this.selectedWorkflow.uid);

		this.executionService.performWorkflowStatusAction(playbook.uid, this.selectedWorkflow.uid, 'execute')
			.then(() => {
				this.toastyService.success(`Successfully started execution of "${playbook.name} - ${this.selectedWorkflow.name}"`);
			})
			.catch(e => this.toastyService.error(`Error executing workflow: ${e.message}`));
	}

	workflowSelectChange(event: any): void {
		if (!event.value || event.value === '') {
			this.selectedWorkflow = null;
		} else {
			this.selectedWorkflow = this.workflows.find(w => w.uid === event.value);
		}
	}

	_getPlaybookFromWorkflowId(workflowId: string): Playbook {
		let playbook: Playbook;
		this.playbooks.forEach(pb => {
			if (playbook) { return; }
			if (pb.workflows.find(w => w.uid === workflowId)) { playbook = pb; }
		});
		return playbook;
	}
}
