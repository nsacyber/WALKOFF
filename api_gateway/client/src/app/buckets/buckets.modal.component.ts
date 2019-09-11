import { Component, Input, ChangeDetectorRef, OnInit, AfterViewInit } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { Bucket } from '../models/buckets/bucket';

@Component({
	selector: 'buckets-modal',
	templateUrl: './buckets.modal.html',
	styleUrls: [
		'./buckets.scss',
	],
})
export class BucketsModalComponent implements OnInit, AfterViewInit {
	@Input() bucket: Bucket = new Bucket();
	@Input() existing: boolean = false;

	constructor(
		public activeModal: NgbActiveModal,
		private cdr: ChangeDetectorRef,
	) { }

	ngOnInit(): void {}

	ngAfterViewInit(): void {
		this.cdr.detectChanges();
	}

	isBasicInfoValid(): boolean {
		return !!(this.bucket.name && this.bucket.name.trim())
	}

	submit(): void {
		if (this.isBasicInfoValid()) { this.activeModal.close(this.bucket) }
	}
}
