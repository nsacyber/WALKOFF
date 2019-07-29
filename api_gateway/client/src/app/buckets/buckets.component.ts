import { Component, ViewEncapsulation, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';
import { Select2OptionData } from 'ng2-select2';
import 'rxjs/add/operator/debounceTime';

import { UtilitiesService } from '../utilities.service';
import { BucketsService } from './buckets.service';

import { BucketsModalComponent } from './buckets.modal.component';

import { Bucket } from '../models/buckets/bucket';

@Component({
	selector: 'buckets-component',
	templateUrl: './buckets.html',
	styleUrls: [
		'./buckets.scss',
		'../../../node_modules/ng-pick-datetime/styles/picker.min.css',
	],
	encapsulation: ViewEncapsulation.None,
	providers: [BucketsService],
})
export class BucketsComponent implements OnInit {
  buckets: Bucket[] = []
  displayBuckets: Bucket[] = [];
  filterQuery: FormControl = new FormControl();

	constructor(
		private bucketsService: BucketsService,
		private modalService: NgbModal,
		private toastrService: ToastrService,
		private utils: UtilitiesService,
	) {}

	/**
	 * On component initialization, get the scheduler status for display/actioning.
	 * Get workflow names to add to a scheduled task.
	 * Get scheduled tasks to display in the data table.
	 * Initialize the search filter input to filter scheduled tasks.
	 */
	ngOnInit(): void {
	  this.getBuckets();

	  this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterBuckets());
	}

  /**
	 * Based on the search filter input, filter out the buckets based on matching some parameters (name, desc.).
	 */
	filterBuckets(): void {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayBuckets = this.buckets.filter((s) => {
			return (s.name.toLocaleLowerCase().includes(searchFilter) ||
				s.description.toString().includes(searchFilter));
		});
	}

	/**
	 * Gets a list of buckets from the server for display in our data table.
	 */
	getBuckets(): void {
		this.bucketsService
			.getAllBuckets()
			.then(buckets => this.displayBuckets = this.buckets = buckets)
			.catch(e => this.toastrService.error(`Error retrieving buckets: ${e.message}`));
	}

  /**
	 * Activates when a row is toggled
	 */
	onDetailToggle(e): void {
	}

	/**
	 * Spawns a modal for adding a new bucket. Passes in our workflow names for usage in the modal.
	 */
	addBucket(): void {
		const modalRef = this.modalService.open(BucketsModalComponent, { size: 'lg' });
		modalRef.componentInstance.title = 'Create a new Bucket';
		modalRef.componentInstance.submitText = 'Add Bucket';

		this._handleModalClose(modalRef);
	}

	/**
	 * On closing an add/edit modal (on clicking save), we will add or update existing scheduled tasks for display.
	 * @param modalRef Modal reference that is being closed
	 */
	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => {
				//Handle modal dismiss
				if (!result || !result.bucket) { return; }

				//On edit, find and update the edited item
				if (result.isEdit) {
					const toUpdate = this.buckets.find(st => st.id === result.bucket.id);
					Object.assign(toUpdate, result.bucket);

					this.filterBuckets();

					this.toastrService.success(`Bucket "${result.buckets.name}" successfully edited.`);
				} else {
					this.buckets.push(result.bucket);

					this.filterBuckets();

					this.toastrService.success(`Buckets "${result.bucket.name}" successfully added.`);
				}
			},
			(error) => { if (error) { this.toastrService.error(error.message); } });
	}
}
