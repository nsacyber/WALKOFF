import { Component, ViewEncapsulation, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';
import { Select2OptionData } from 'ng2-select2';
import 'rxjs/add/operator/debounceTime';

import { SchedulerModalComponent } from './scheduler.modal.component';

import { SchedulerService } from './scheduler.service';
import { UtilitiesService } from '../utilities.service';

import { ScheduledTask } from '../models/scheduler/scheduledTask';

@Component({
	selector: 'scheduler-component',
	templateUrl: './scheduler.html',
	styleUrls: [
		'./scheduler.scss',
		'../../../node_modules/ng-pick-datetime/styles/picker.min.css',
	],
	encapsulation: ViewEncapsulation.None,
	providers: [SchedulerService],
})
export class SchedulerComponent implements OnInit {
	schedulerStatus: string;
	scheduledTasks: ScheduledTask[] = [];
	displayScheduledTasks: ScheduledTask[] = [];
	availableWorkflows: Select2OptionData[] = [];

	filterQuery: FormControl = new FormControl();

	constructor(
		private schedulerService: SchedulerService, private modalService: NgbModal,
		private toastrService: ToastrService, private utils: UtilitiesService,
	) {}

	/**
	 * On component initialization, get the scheduler status for display/actioning.
	 * Get workflow names to add to a scheduled task.
	 * Get scheduled tasks to display in the data table.
	 * Initialize the search filter input to filter scheduled tasks.
	 */
	ngOnInit(): void {

		this.getSchedulerStatus();
		this.getWorkflows();
		this.getScheduledTasks();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterScheduledTasks());
	}

	/**
	 * Based on the search filter input, filter out the scheduled tasks based on matching some parameters (name, desc.).
	 */
	filterScheduledTasks(): void {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayScheduledTasks = this.scheduledTasks.filter((s) => {
			return (s.name.toLocaleLowerCase().includes(searchFilter) ||
				s.description.toString().includes(searchFilter));
		});
	}

	/**
	 * Gets the scheduler status from the server (e.g. 'paused').
	 */
	getSchedulerStatus(): void {
		this.schedulerService
			.getSchedulerStatus()
			.then(schedulerStatus => this.schedulerStatus = schedulerStatus)
			.catch(e => this.toastrService.error(`Error retrieving scheduler status: ${e.message}`));
	}

	/**
	 * Changes the status of the scheduler and updates the local scheduler status to reflect that.
	 * @param status Status to change to
	 */
	changeSchedulerStatus(status: string): void {
		if (status === 'start' && this.schedulerStatus === 'paused') { status = 'resume'; }

		this.schedulerService
			.changeSchedulerStatus(status)
			.then(newStatus => {
				if (newStatus) { this.schedulerStatus = newStatus; }
			})
			.catch(e => this.toastrService.error(`Error changing scheduler status: ${e.message}`));
	}

	/**
	 * Gets a list of scheduled tasks from the server for display in our data table.
	 */
	getScheduledTasks(): void {
		this.schedulerService
			.getAllScheduledTasks()
			.then(scheduledTasks => this.displayScheduledTasks = this.scheduledTasks = scheduledTasks)
			.catch(e => this.toastrService.error(`Error retrieving scheduled tasks: ${e.message}`));
	}

	/**
	 * Spawns a modal for adding a new scheduled task. Passes in our workflow names for usage in the modal.
	 */
	addScheduledTask(): void {
		const modalRef = this.modalService.open(SchedulerModalComponent, { size: 'lg' });
		modalRef.componentInstance.title = 'Schedule a New Task';
		modalRef.componentInstance.submitText = 'Add Scheduled Task';
		modalRef.componentInstance.availableWorkflows = this.availableWorkflows;

		this._handleModalClose(modalRef);
	}

	/**
	 * Spawns a modal for editing an existing scheduled task. Passes in our workflow names for usage in the modal.
	 */
	editScheduledTask(task: ScheduledTask): void {
		const modalRef = this.modalService.open(SchedulerModalComponent, { size: 'lg' });
		modalRef.componentInstance.title = `Edit Task ${task.name}`;
		modalRef.componentInstance.submitText = 'Save Changes';
		modalRef.componentInstance.availableWorkflows = this.availableWorkflows;
		modalRef.componentInstance.workingScheduledTask = this.utils.cloneDeep(task);
		delete modalRef.componentInstance.workingScheduledTask.$$index;

		this._handleModalClose(modalRef);

	}

	/**
	 * After user confirmation, will delete a given scheduled task from the database.
	 * Removes it from our list of scheduled tasks to display.
	 * @param taskToDelete Scheduled Task to delete
	 */
	async deleteScheduledTask(taskToDelete: ScheduledTask) {
		await this.utils.confirm(`Are you sure you want to delete <b>${taskToDelete.name}</b>?`);

		this.schedulerService
			.deleteScheduledTask(taskToDelete.id)
			.then(() => {
				this.scheduledTasks = this.scheduledTasks.filter(scheduledTask => scheduledTask.id !== taskToDelete.id);

				this.filterScheduledTasks();

				this.toastrService.success(`Scheduled Task "${taskToDelete.name}" successfully deleted.`);
			})
			.catch(e => this.toastrService.error(`Error deleting task: ${e.message}`));
	}

	/**
	 * Tells the server to change the status of a scheduled task (e.g. 'pause').
	 * Updates the local scheduled task on success to reflect this change.
	 * @param task Scheduled Task to change the status of
	 * @param actionName Action to take on the task
	 */
	changeScheduledTaskStatus(task: ScheduledTask, actionName: string): void {
		let newStatus: string;

		switch (actionName) {
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
				this.toastrService.error(`Attempted to set an unknown status ${actionName}`);
				break;
		}

		if (!newStatus) { return; }

		this.schedulerService
			.changeScheduledTaskStatus(task.id, actionName)
			.then(() => {
				task.status = newStatus;
			})
			.catch(e => this.toastrService.error(`Error changing scheduler status: ${e.message}`));
	}

	/**
	 * Grabs an array of playbooks/workflows from the server (id, name pairs).
	 * From this array, creates an array of Select2Option data with the id and playbook/workflow name.
	 */
	getWorkflows(): void {
		this.schedulerService
			.getWorkflows()
			.then(workflows => {
				workflows.forEach(workflow => {
					this.availableWorkflows.push({
						id: workflow.id,
						text: `${workflow.name}`,
					});
				});
			});
	}

	/**
	 * Converts the task_trigger of a scheduled task into a readable string for display in the datatable.
	 * @param scheduledTask Scheduled task to convert the task_trigger of
	 */
	getRule(scheduledTask: ScheduledTask): string {
		//stringify only the truthy args (aka those specified) [seems that the server only returns args that are specified]
		// let out = _.pick(scheduledTask.task_trigger.args, function(value: any) {
		// 	return value;
		// });

		let rule = JSON.stringify(scheduledTask.task_trigger.args, null, 1);

		rule = rule.substr(1, rule.length - 2).replace(/"/g, '');

		return rule;
	}

	/**
	 * Converts the workflow ids array of a scheduled task into a readable string for display in the datatable.
	 * @param scheduledTask Scheduled task to convert the workflows of
	 */
	getFriendlyWorkflows(scheduledTask: ScheduledTask): string {
		if (!this.availableWorkflows || !scheduledTask.workflows || !scheduledTask.workflows.length) { return ''; }

		return this.availableWorkflows.filter(workflow => {
			return scheduledTask.workflows.indexOf(workflow.id) >= 0;
		}).map(workflow => workflow.text).join(', ');
	}

	/**
	 * On closing an add/edit modal (on clicking save), we will add or update existing scheduled tasks for display.
	 * @param modalRef Modal reference that is being closed
	 */
	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => {
				//Handle modal dismiss
				if (!result || !result.scheduledTask) { return; }

				//On edit, find and update the edited item
				if (result.isEdit) {
					const toUpdate = this.scheduledTasks.find(st => st.id === result.scheduledTask.id);
					Object.assign(toUpdate, result.scheduledTask);

					this.filterScheduledTasks();

					this.toastrService.success(`Scheduled task "${result.scheduledTask.name}" successfully edited.`);
				} else {
					this.scheduledTasks.push(result.scheduledTask);

					this.filterScheduledTasks();

					this.toastrService.success(`Scheduled task "${result.scheduledTask.name}" successfully added.`);
				}
			},
			(error) => { if (error) { this.toastrService.error(error.message); } });
	}
}
