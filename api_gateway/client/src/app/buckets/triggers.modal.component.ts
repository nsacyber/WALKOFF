import { Component, Input, OnInit } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { BucketTrigger } from '../models/buckets/trigger';
import { Workflow } from '../models/playbook/workflow';

@Component({
	selector: 'triggers-modal',
	templateUrl: './triggers.modal.html',
	styleUrls: [
		'./buckets.scss',
	],
})
export class TriggersModalComponent implements OnInit {
	@Input() trigger: BucketTrigger;
	@Input() workflows: Workflow[];
	@Input() existing: boolean = false;

	constructor(public activeModal: NgbActiveModal) { }

	ngOnInit(): void {}

	isBasicInfoValid(): boolean {
		return this.trigger.event_type && this.trigger.workflow.length > 0;
	}

	submit(): void {
		if (this.isBasicInfoValid()) { this.activeModal.close(this.trigger) }
	}
}
