import { Component, Input, OnInit } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import { Select2OptionData } from 'ng2-select2';
import * as moment from 'moment';

import { SchedulerService } from './scheduler.service';

import { ScheduledTask } from '../models/scheduledTask';
import { ScheduledTaskCron } from '../models/scheduledTaskCron';
import { ScheduledTaskInterval } from '../models/scheduledTaskInterval';
import { ScheduledTaskDate } from '../models/scheduledTaskDate';
import { GenericObject } from '../models/genericObject';

@Component({
	selector: 'scheduler-modal',
	templateUrl: 'client/scheduler/scheduler.modal.html',
	styleUrls: [
		'client/scheduler/scheduler.css',
	],
	providers: [SchedulerService],
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
		private schedulerService: SchedulerService, private activeModal: NgbActiveModal,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig) {}

	ngOnInit(): void {
		this.toastyConfig.theme = 'bootstrap';

		this.workflowSelectConfig = {
			width: '100%',
			multiple: true,
			allowClear: true,
			placeholder: 'Select workflow(s) to run...',
			closeOnSelect: false,
		};
	}

	submit(): void {
		const validationMessage = this.validate();
		if (validationMessage) {
			this.toastyService.error(validationMessage);
			return;
		}

		this.convertStringsToInt(this.workingScheduledTask.task_trigger.args);

		//If device has an ID, device already exists, call update
		if (this.workingScheduledTask.id) {
			this.schedulerService
				.editScheduledTask(this.workingScheduledTask)
				.then(scheduledTask => this.activeModal.close({
					scheduledTask,
					isEdit: true,
				}))
				.catch(e => this.toastyService.error(e.message));
		} else {
			this.schedulerService
				.addScheduledTask(this.workingScheduledTask)
				.then(scheduledTask => this.activeModal.close({
					scheduledTask,
					isEdit: false,
				}))
				.catch(e => this.toastyService.error(e.message));
		}
	}

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

	changeType(e: string): void {
		switch (e) {
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

	workflowsSelectChanged(e: any): void {
		this.workingScheduledTask.workflows = e.value;
	}

	getToday(): string {
		return moment().format('YYYY-MM-DD');
	}

	convertStringsToInt(args: any): void {
		if (typeof(args) !== 'object') { return; }
		for (const [key, value] of Object.entries(args)) {
			const newVal = +value;
			if (typeof(value) !== 'string') { return; }
			args[key] = newVal;
		}
	}
}
