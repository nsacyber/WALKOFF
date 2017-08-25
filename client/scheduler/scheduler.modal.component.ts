import { Component, Input } from '@angular/core';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';
import { Select2OptionData } from 'ng2-select2';
import * as moment from 'moment';

import { SchedulerService } from './scheduler.service';

import { ScheduledTask } from '../models/scheduledTask';
import { ScheduledTaskCron } from '../models/scheduledTaskCron';
import { ScheduledTaskInterval } from '../models/scheduledTaskInterval';
import { ScheduledTaskDate } from '../models/scheduledTaskDate';
 
@Component({
	selector: 'scheduler-modal',
	templateUrl: 'client/scheduler/scheduler.modal.html',
	styleUrls: [
		'client/scheduler/scheduler.css'
	],
	providers: [SchedulerService]
})
export class SchedulerModalComponent {
	@Input() workingScheduledTask: ScheduledTask = new ScheduledTask();
	@Input() title: string;
	@Input() submitText: string;
	@Input() availableWorkflows: Select2OptionData[] = [];

	scheduledItemTriggerTypes: string[] = ['date', 'interval', 'cron'];
	workflowSelectConfig: Select2Options;
	cron: ScheduledTaskCron = new ScheduledTaskCron();
	interval: ScheduledTaskInterval = new ScheduledTaskInterval();
	date: ScheduledTaskDate = new ScheduledTaskDate();
	
	constructor(private schedulerService: SchedulerService, private activeModal: NgbActiveModal, private toastyService: ToastyService, private toastyConfig: ToastyConfig) {
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
		let validationMessage = this.validate();
		if (validationMessage) {
			this.toastyService.error(validationMessage);
			return;
		}

		this.convertStringsToInt(this.workingScheduledTask.scheduler.args);

		//If device has an ID, device already exists, call update
		if (this.workingScheduledTask.id) {
			this.schedulerService
				.editScheduledTask(this.workingScheduledTask)
				.then(scheduledTask => this.activeModal.close({
					scheduledTask: scheduledTask,
					isEdit: true
				}))
				.catch(e => this.toastyService.error(e.message));
		}
		else {
			this.schedulerService
				.addScheduledTask(this.workingScheduledTask)
				.then(scheduledTask => this.activeModal.close({
					scheduledTask: scheduledTask,
					isEdit: false
				}))
				.catch(e => this.toastyService.error(e.message));
		}
	}

	validate(): string {
		let args: any = this.workingScheduledTask.scheduler.args;

		if (this.workingScheduledTask.scheduler.type === 'interval' || this.workingScheduledTask.scheduler.type === 'cron') {
			let startDate = +args.start_date;
			let endDate = +args.end_date;

			if (startDate > endDate) return 'The end date cannot be before the start date.';
		}

		if (this.workingScheduledTask.scheduler.type === 'interval') {
			if (!args.weeks && !args.days && !args.hours && !args.minutes && !args.seconds)
				return 'You must specify some interval of time for the actions to occur.';
		}

		if (this.workingScheduledTask.scheduler.type === 'cron') {
			if (!args.year && !args.month && !args.day && !args.week && !args.day_of_week && !args.hour && !args.minute && !args.second)
				return 'You must specify some cron parameters for the actions to occur.';
		}

		return '';
	}

	changeType(e: string): void {
		switch (e) {
			case 'cron':
				this.workingScheduledTask.scheduler.args = this.cron;
				break;
			case 'interval':
				this.workingScheduledTask.scheduler.args = this.interval;
				break;
			case 'date':
				this.workingScheduledTask.scheduler.args = this.date;
				break;
			default:
				this.workingScheduledTask.scheduler.args = null;
				break;
		}

		console.log(this.workingScheduledTask);
	}

	getToday(): string {
		return moment().format('YYYY-MM-DD');
	}

	convertStringsToInt(args: any): void {
		for (let [key, value] of Object.entries(args)) {
			let newVal = +value;
			if (typeof(value) !== 'string') return;
			args[key] = newVal;
		}
	}
}