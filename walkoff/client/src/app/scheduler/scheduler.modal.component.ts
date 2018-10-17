import { Component, Input, OnInit } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';
import { Select2OptionData } from 'ng2-select2';
import * as moment from 'moment';

import { SchedulerService } from './scheduler.service';
import { UtilitiesService } from '../utilities.service';

import { ScheduledTask } from '../models/scheduler/scheduledTask';
import { ScheduledTaskCron } from '../models/scheduler/scheduledTaskCron';
import { ScheduledTaskInterval } from '../models/scheduler/scheduledTaskInterval';
import { ScheduledTaskDate } from '../models/scheduler/scheduledTaskDate';
import { GenericObject } from '../models/genericObject';

@Component({
	selector: 'scheduler-modal',
	templateUrl: './scheduler.modal.html',
	styleUrls: [
		'./scheduler.scss',
	],
	providers: [SchedulerService, UtilitiesService],
})
export class SchedulerModalComponent implements OnInit {
	@Input() workingScheduledTask: ScheduledTask = new ScheduledTask();
	@Input() title: string;
	@Input() submitText: string;
	@Input() availableWorkflows: Select2OptionData[] = [];

	scheduledItemTriggerTypes: string[] = ['date', 'interval', 'cron'];
	workflowSelectConfig: Select2Options;
	cron: ScheduledTaskCron = new ScheduledTaskCron();
	interval: ScheduledTaskInterval = new ScheduledTaskInterval();
	date: ScheduledTaskDate = new ScheduledTaskDate();
	
	constructor(
		private schedulerService: SchedulerService, public activeModal: NgbActiveModal,
		private toastrService: ToastrService,
	) {}

	/**
	 * Initializes the workflow select config for selecting workflows to schedule.
	 */
	ngOnInit(): void {

		this.workflowSelectConfig = {
			width: '100%',
			multiple: true,
			allowClear: true,
			placeholder: 'Select workflow(s) to run...',
			closeOnSelect: false,
		};
	}

	/**
	 * Adds a new / updates an existing scheduled task. Will also convert fields under task trigger to int if applicable.
	 */
	submit(): void {
		const validationMessage = this.validate();
		if (validationMessage) {
			this.toastrService.error(validationMessage);
			return;
		}

		if (this.workingScheduledTask.task_trigger.type === 'cron') {
			this.convertStringsToInt(this.workingScheduledTask.task_trigger.args);
		}

		//If device has an ID, device already exists, call update
		if (this.workingScheduledTask.id) {
			this.schedulerService
				.editScheduledTask(this.workingScheduledTask)
				.then(scheduledTask => this.activeModal.close({
					scheduledTask,
					isEdit: true,
				}))
				.catch(e => this.toastrService.error(e.message));
		} else {
			this.schedulerService
				.addScheduledTask(this.workingScheduledTask)
				.then(scheduledTask => this.activeModal.close({
					scheduledTask,
					isEdit: false,
				}))
				.catch(e => this.toastrService.error(e.message));
		}
	}

	/**
	 * Validates a scheduled task. Checks basic info (name, workflows specified).
	 * Ensures args is specifies as well as a start date. Ensures that end date is not before start date.
	 * If it's an interval or cron, checks if any other param exists in args.
	 */
	validate(): string {
		if (!this.workingScheduledTask.name) { return 'A name is required.'; }
		if (!this.workingScheduledTask.workflows || !this.workingScheduledTask.workflows.length) {
			return 'Please specify at least one workflow to be run.';
		}

		const args: any = this.workingScheduledTask.task_trigger.args;

		if (!args) { return 'Please select a type and fill out the trigger parameters.'; }

		if (!(args.start_date || args.run_date)) { return 'A start date is required.'; }

		if (this.workingScheduledTask.task_trigger.type === 'interval' || 
			this.workingScheduledTask.task_trigger.type === 'cron') {
			const startDate = +args.start_date;
			const endDate = +args.end_date;

			if (startDate > endDate) { return 'The end date cannot be before the start date.'; }
		}

		if (this.workingScheduledTask.task_trigger.type === 'interval') {
			if (!this._doesArgsHaveAnything(args)) {
				return 'You must specify some interval of time for the actions to occur.';
			}
		}

		if (this.workingScheduledTask.task_trigger.type === 'cron') {
			if (!this._doesArgsHaveAnything(args)) {
				return 'You must specify some cron parameters for the actions to occur.';
			}
		}

		return '';
	}

	/**
	 * Checks if this args object has any value other than start/end date.
	 * @param args Args object to check against
	 */
	_doesArgsHaveAnything(args: GenericObject) {
		let ret = false;
		Object.keys(args).forEach(key => {
			// Will reject falsy values (including 0 as that is not an applicable value here)
			// Will also ignore start/end dates here
			if (ret || key === 'start_date' || key === 'end_date' || !args[key]) { return; }

			// For strings, trim and check if they're wildcards (0/*)
			if (typeof(args[key]) === 'string') {
				args[key] = (args[key] as string).trim();
				if (args[key] && !(args[key] === '0' || args[key] === '*')) { ret = true; }
			// For other types (int), return true (aka it's != 0)
			} else {
				ret = true;
			}
		});

		return ret;
	}

	/**
	 * Switches between the types of scheduled task on the working scheduled task
	 * (all stored locally so we don't lose information if we switch type).
	 * @param type Event value from the type select.
	 */
	changeType(type: string): void {
		switch (type) {
			case 'cron':
				this.workingScheduledTask.task_trigger.args = this.cron;
				break;
			case 'interval':
				this.workingScheduledTask.task_trigger.args = this.interval;
				break;
			case 'date':
				this.workingScheduledTask.task_trigger.args = this.date;
				break;
			default:
				this.workingScheduledTask.task_trigger.args = null;
				break;
		}
	}

	/**
	 * Updates the working scheduled task's workflows from the event value.
	 * @param event JS Event from workflows select2
	 */
	workflowsSelectChanged(event: any): void {
		this.workingScheduledTask.workflows = event.value;
	}

	/**
	 * Returns today's date to be used in initializing the minimum date in our date selector.
	 */
	getToday(): string {
		return moment().format('YYYY-MM-DD');
	}

	/**
	 * For each value in the args object that can convert to number, convert it to number.
	 * @param args Args object to check
	 */
	convertStringsToInt(args: any): void {
		if (typeof(args) !== 'object') { return; }
		for (const [key, value] of Object.entries(args)) {
			if (key === 'start_date' || key === 'end_date') { return; }
			if (isNaN(value as number)) { return; }
			args[key] = +value;
		}
	}
}
