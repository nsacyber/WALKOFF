import { Component, Input, ChangeDetectorRef, ViewChild, ElementRef, OnInit, AfterViewInit } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';
import { Select2OptionData } from 'ng2-select2';
import { UtilitiesService } from '../utilities.service';

import { BucketsService } from './buckets.service';
import { BucketTrigger } from '../models/buckets/trigger';

@Component({
	selector: 'triggers-modal',
	templateUrl: './triggers.modal.html',
	styleUrls: [
		'./buckets.scss',
	],
	providers: [UtilitiesService],
})
export class TriggersModalComponent implements OnInit, AfterViewInit {
  @Input() trigger: BucketTrigger = new BucketTrigger();
  @Input() title: string;
  @Input() submitText: string;
  @Input() availableWorkflows: Select2OptionData[] = [];

  existing: boolean = false;

  workflowSelectConfig: Select2Options;

	constructor (
		private bucketsService: BucketsService, public activeModal: NgbActiveModal,
		private toastrService: ToastrService, private cdr: ChangeDetectorRef,
	) {}

	ngOnInit(): void {
	  this.trigger.workflow = "";
	  this.workflowSelectConfig = {
			width: '100%',
			multiple: false,
			allowClear: true,
			placeholder: 'Select workflow to run on trigger...',
			closeOnSelect: false,
		};
	}

	ngAfterViewInit(): void {
	}

	/**
	 * Submits the add/edit bucket modal.
	 */
	submit(): void {
    if (!this.isBasicInfoValid()) { return; }
  }


  isBasicInfoValid(): boolean {
		if (this.trigger.event_type && this.trigger.workflow.length) { return true; }
		return false;
	}

  	/**
	 * Updates the working scheduled task's workflows from the event value.
	 * @param event JS Event from workflows select2
	 */
	workflowsSelectChanged(event: any): void {
		this.trigger.workflow = event.value;
	}

}
