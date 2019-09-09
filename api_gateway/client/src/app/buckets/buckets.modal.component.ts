import { Component, Input, ChangeDetectorRef, ViewChild, ElementRef, OnInit, AfterViewInit } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';

import { BucketsService } from './buckets.service';
import { UtilitiesService } from '../utilities.service';

import { Bucket } from '../models/buckets/bucket';

@Component({
	selector: 'buckets-modal',
	templateUrl: './buckets.modal.html',
	styleUrls: [
		'./buckets.scss',
	],
	providers: [BucketsService, UtilitiesService],
})
export class BucketsModalComponent implements OnInit, AfterViewInit {
  @Input() bucket: Bucket = new Bucket();
  @Input() title: string;
  @Input() submitText: string;
  existing: boolean = false;


	constructor (
		private bucketsService: BucketsService, public activeModal: NgbActiveModal,
		private toastrService: ToastrService, private cdr: ChangeDetectorRef,
	) {}

	ngOnInit(): void {
	}

	ngAfterViewInit(): void {
	  this.cdr.detectChanges();
	}

	/**
	 * Submits the add/edit bucket modal.
	 */
	submit(): void {
    if (!this.isBasicInfoValid()) { return; }
  }


  isBasicInfoValid(): boolean {
		if (this.bucket.name && this.bucket.name.trim()) { return true; }
		return false;
	}

}
