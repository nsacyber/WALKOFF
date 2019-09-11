import { Component, ViewEncapsulation, OnInit, ViewChild } from '@angular/core';
import { FormControl } from '@angular/forms';
import { NgbModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';

import { UtilitiesService } from '../utilities.service';
import { BucketsService } from './buckets.service';

import { BucketsModalComponent } from './buckets.modal.component';
import { TriggersModalComponent } from './triggers.modal.component';

import { Bucket } from '../models/buckets/bucket';
import { BucketTrigger } from '../models/buckets/trigger';
import { Workflow } from '../models/playbook/workflow';

@Component({
	selector: 'buckets-component',
	templateUrl: './buckets.html',
	styleUrls: [
		'./buckets.scss',
		'../../../node_modules/ng-pick-datetime/styles/picker.min.css',
	],
	encapsulation: ViewEncapsulation.None,
})
export class BucketsComponent implements OnInit {
	buckets: Bucket[] = [];
	workflows: Workflow[] = [];
	filterQuery: FormControl = new FormControl();

	@ViewChild('bucketsTable', { static: false }) table: any;

	constructor(
		private bucketsService: BucketsService,
		private modalService: NgbModal,
		private toastrService: ToastrService,
		private utils: UtilitiesService,
	) { }

	/**
	 * On component initialization, get the scheduler status for display/actioning.
	 * Get workflow names to add to a scheduled task.
	 * Get scheduled tasks to display in the data table.
	 * Initialize the search filter input to filter scheduled tasks.
	 */
	ngOnInit(): void {
		this.bucketsService.bucketsChange.subscribe(buckets => this.buckets = buckets);
		this.bucketsService.getWorkflows().then(workflows => this.workflows = workflows);
	}

	/**
	   * Based on the search filter input, filter out the buckets based on matching some parameters (name, desc.).
	   */
	get filterBuckets(): Bucket[] {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';
		return this.buckets.filter(bucket =>
			bucket.name.toLocaleLowerCase().includes(searchFilter) ||
			bucket.description.toLocaleLowerCase().includes(searchFilter) ||
			(bucket.description && bucket.description.toLocaleLowerCase().includes(searchFilter))
		)
	}

	/**
	 * Spawns a modal for adding a new bucket. Passes in our workflow names for usage in the modal.
	 */
	addBucket(): void {
		const modalRef = this.modalService.open(BucketsModalComponent, { size: 'lg' });
		modalRef.result.then(bucket => {
			this.bucketsService.addBucket(bucket).then(() => {
				this.toastrService.success(`Added <b>${bucket.name}</b>`);
			})
		}, () => null)
	}

	editBucket(bucket: Bucket): void {
		const modalRef = this.modalService.open(BucketsModalComponent, { size: 'lg' });
		modalRef.componentInstance.existing = true;
		modalRef.componentInstance.bucket = bucket.clone();

		modalRef.result.then(bucket => {
			this.bucketsService.editBucket(bucket).then(() => {
				this.toastrService.success(`Added <b>${bucket.name}</b>`);
			})
		}, () => null)
	}

	async deleteBucket(bucketToDelete: Bucket) {
		await this.utils.confirm(`Are you sure you want to delete <b>${bucketToDelete.name}</b>?`);
		this.bucketsService
			.deleteBucket(bucketToDelete)
			.then(() => this.toastrService.success(`Deleted <b>${bucketToDelete.name}</b>`))
			.catch(e => this.toastrService.error(`Error deleting <b>${e.message}</b>`));
	}

	addTrigger(bucket: Bucket): void {
		const modalRef = this.modalService.open(TriggersModalComponent, { size: 'lg' });
		modalRef.componentInstance.trigger = new BucketTrigger(bucket.id);
		modalRef.componentInstance.workflows = this.workflows;

		modalRef.result.then(trigger => {
			this.bucketsService.addTrigger(trigger).then(() => {
				this.toastrService.success(`Saved Trigger`);
			})
		}, () => null)
	}

	editTrigger(trigger: BucketTrigger): void {
		const modalRef = this.modalService.open(TriggersModalComponent, { size: 'lg' });
		modalRef.componentInstance.workflows = this.workflows;
		modalRef.componentInstance.trigger = trigger.clone();
		modalRef.componentInstance.existing = true;

		modalRef.result.then(trigger => {
			this.bucketsService.editTrigger(trigger).then(() => {
				this.toastrService.success(`Saved Trigger`);
			})
		}, () => null)
	}

	async deleteTrigger(trigger: BucketTrigger) {
		await this.utils.confirm(`Are you sure you want to delete <b>${trigger.id}</b>?`);
		this.bucketsService.deleteTrigger(trigger)
			.then(() => this.toastrService.success(`Deleted <b>${trigger.id}</b>`))
			.catch(e => this.toastrService.error(`Error deleting <b>${e.message}</b>`));
	}

	toggleExpandRow(row) {
		//    console.log('Toggled Expand Row!', row);
		this.table.rowDetail.toggleExpandRow(row);
	}

	onDetailToggle(event) {
		//    console.log('Detail Toggled', event);
	}

	getWorkflowName(id: string) {
		return this.workflows.find(w => w.id == id).name;
	}
}
