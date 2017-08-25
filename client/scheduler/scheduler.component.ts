import { Component } from '@angular/core';
import { FormControl } from '@angular/forms';
import * as _ from 'lodash';
import { NgbModal, NgbActiveModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';
import { Select2OptionData } from 'ng2-select2';
import "rxjs/add/operator/debounceTime";

import { SchedulerModalComponent } from './scheduler.modal.component';

import { SchedulerService } from './scheduler.service';

import { AvailableSubscription } from '../models/availableSubscription';
import { Case } from '../models/case';
import { Workflow } from '../models/workflow';
import { ScheduledTask } from '../models/scheduledTask';

@Component({
	selector: 'scheduler-component',
	templateUrl: 'client/scheduler/scheduler.html',
	styleUrls: [
		'client/scheduler/scheduler.css',
	],
	providers: [SchedulerService]
})
export class SchedulerComponent {
	currentController: string;
	schedulerStatus: string;
	scheduledTasks: ScheduledTask[] = [];
	displayScheduledTasks: ScheduledTask[] = [];
	availableWorkflows: Select2OptionData[] = [];

	filterQuery: FormControl = new FormControl();

	constructor(private schedulerService: SchedulerService, private modalService: NgbModal, private toastyService:ToastyService, private toastyConfig: ToastyConfig) {
		this.currentController = "Default Controller";
		this.toastyConfig.theme = 'bootstrap';

		this.getSchedulerStatus();
		this.getWorkflowNames();
		this.getScheduledTasks();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterScheduledTasks());
	}

	filterScheduledTasks(): void {
		let searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayScheduledTasks = this.scheduledTasks.filter((s) => {
			return (s.name.toLocaleLowerCase().includes(searchFilter) ||
				s.description.toString().includes(searchFilter));
		});
	}

	getSchedulerStatus(): void {
		this.schedulerService
			.getSchedulerStatus()
			.then(schedulerStatus => this.schedulerStatus = schedulerStatus)
			.catch(e => this.toastyService.error(`Error retrieving scheduler status: ${e.message}`));
	}

	changeSchedulerStatus(status: string): void {
		if (status === 'start' && this.schedulerStatus === 'paused') status = 'resume';

		this.schedulerService
			.changeSchedulerStatus(status)
			.then((newStatus) => {
				if (newStatus) this.schedulerStatus = newStatus;
			})
			.catch(e => this.toastyService.error(`Error changing scheduler status: ${e.message}`));
	}

	executeWorkflow(workflow: Workflow): void {
		this.schedulerService
			.executeWorkflow(workflow.name, workflow.name)
			.then(() => this.toastyService.success(`Workflow ${workflow.name} has been scheduled to execute.`))
			.catch(e => this.toastyService.error(`Error executing workflow: ${e.message}`));
	}

	getScheduledTasks(): void {
		this.schedulerService
			.getScheduledTasks()
			.then(scheduledTasks => this.displayScheduledTasks = this.scheduledTasks = scheduledTasks)
			.catch(e => this.toastyService.error(`Error retrieving scheduled tasks: ${e.message}`));
	}

	addScheduledTask(): void {
		const modalRef = this.modalService.open(SchedulerModalComponent, { size: 'lg' });
		modalRef.componentInstance.title = 'Schedule a New Task';
		modalRef.componentInstance.submitText = 'Add Scheduled Task';
		modalRef.componentInstance.availableWorkflows = this.availableWorkflows;

		this._handleModalClose(modalRef);
	}

	editScheduledTask(task: ScheduledTask): void {
		const modalRef = this.modalService.open(SchedulerModalComponent, { size: 'lg' });
		modalRef.componentInstance.title = `Edit Task ${task.name}`;
		modalRef.componentInstance.submitText = 'Save Changes';
		modalRef.componentInstance.availableWorkflows = this.availableWorkflows;

		modalRef.componentInstance.workingScheduledTask = _.cloneDeep(task);
		delete modalRef.componentInstance.workingScheduledTask.$$index;

		this._handleModalClose(modalRef);

	}

	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => {
				//Handle modal dismiss
				if (!result || !result.scheduledTask) return;

				//On edit, find and update the edited item
				if (result.isEdit) {
					let toUpdate = _.find(this.scheduledTasks, st => st.id === result.scheduledTask.id);
					Object.assign(toUpdate, result.scheduledTasks);

					this.filterScheduledTasks();

					this.toastyService.success(`Scheduled task "${result.scheduledTask.name}" successfully edited.`);
				}
				//On add, push the new item
				else {
					this.scheduledTasks.push(result.scheduledTask);

					this.filterScheduledTasks();

					this.toastyService.success(`Scheduled task "${result.scheduledTask.name}" successfully added.`);
				}
			},
			(error) => { if (error) this.toastyService.error(error.message); });
	}

	deleteScheduledTask(taskToDelete: ScheduledTask): void {
		if (!confirm(`Are you sure you want to delete the scheduled task "${taskToDelete.name}"?`)) return;

		this.schedulerService
			.deleteScheduledTask(taskToDelete.id)
			.then(() => {
				this.scheduledTasks = _.reject(this.scheduledTasks, scheduledTask => scheduledTask.id === taskToDelete.id);

				this.filterScheduledTasks();

				this.toastyService.success(`Scheduled Task "${taskToDelete.name}" successfully deleted.`);
			})
			.catch(e => this.toastyService.error(`Error deleting task: ${e.message}`));
	}

	changeScheduledTaskStatus(task: ScheduledTask, action: string): void {
		let newStatus: string;

		switch (action) {
			case 'start':
				newStatus = 'running';
				break;
			case 'pause':
				newStatus = 'paused';
				break;
			case 'stop':
				newStatus = 'stopped';
				break;
			default:
				this.toastyService.error(`Attempted to set an unknown status ${action}`);
				break;
		}

		if (!newStatus) return;

		this.schedulerService
			.changeScheduledTaskStatus(task.id, action)
			.then(() => {
				this.schedulerStatus = newStatus;
			})
			.catch(e => this.toastyService.error(`Error changing scheduler status: ${e.message}`));
	}

	// enableScheduledTask(task: ScheduledTask): void {
	// 	this.schedulerService
	// 		.enableScheduledTask(task.id)
	// 		.then(() => task.status = 'enabled')
	// 		.catch(e => this.toastyService.error(`Error enabling task: ${e.message}`));
	// }

	// disableScheduledTask(task: ScheduledTask): void {
	// 	this.schedulerService
	// 		.disableScheduledTask(task.id)
	// 		.then(() => task.status = 'disabled')
	// 		.catch(e => this.toastyService.error(`Error disabling task: ${e.message}`));
	// }

	getWorkflowNames(): void {
		let self = this;

		this.schedulerService
			.getPlaybooks()
			.then((playbooks) => {
				//[ { name: <name>, workflows: [ { name: <name>, uid: <uid> } ] }, ... ]
				playbooks.forEach(function (pb: any) {
					pb.workflows.forEach(function (w: any) {
						self.availableWorkflows.push({
							id: w.uid,
							text: `${pb.name} - ${w.name}`
						});
					});
				})

				// playbooks = _.map(playbooks, function (workflows: any, playbook) {
				// 	workflows = _.map(workflows, function (w: string) {
				// 		return [playbook, w];
				// 	});

				// 	return workflows;
				// });

				// playbooks = _.flatten(playbooks);

				// this.workflowNames = _.map(playbooks, function (pb: string[]) {
				// 	return `${pb[0]} - ${pb[1]}`;
				// });
			});
	}

	getRule(scheduledTask: ScheduledTask): string {
		console.log(scheduledTask);
		//stringify only the truthy args (aka those specified)
		return JSON.stringify(_.pick(scheduledTask.task_trigger.args, _.identity), null, 2);
	}
}