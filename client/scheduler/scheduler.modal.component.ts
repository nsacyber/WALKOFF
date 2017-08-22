import { Component, Input } from '@angular/core';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';
import { Select2OptionData } from 'ng2-select2';

import { SchedulerService } from './scheduler.service';

import { ScheduledTask } from '../models/scheduledTask';
 
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

	constructor(private schedulerService: SchedulerService, private activeModal: NgbActiveModal, private toastyService: ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';

		this.workflowSelectConfig = {
			width: '100%',
			multiple: true,
			allowClear: true,
			placeholder: 'Select workflow(s) to rnu...',
			closeOnSelect: false,
		};
	}

	submit(): void {
		if (!this.validate()) return;

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

	validate(): boolean {
		return true;
	}
}