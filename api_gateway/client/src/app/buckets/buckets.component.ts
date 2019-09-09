import { Component, ViewEncapsulation, OnInit, ViewChild } from '@angular/core';
import { FormControl } from '@angular/forms';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';
import { Select2OptionData } from 'ng2-select2';
import 'rxjs/add/operator/debounceTime';
import { Observable, Subscriber } from 'rxjs';

import { UtilitiesService } from '../utilities.service';
import { BucketsService } from './buckets.service';

import { BucketsModalComponent } from './buckets.modal.component';
import { TriggersModalComponent } from './triggers.modal.component';

import { Bucket } from '../models/buckets/bucket';
import { BucketTrigger } from '../models/buckets/trigger';

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
  buckets: Bucket[] = []
  filterQuery: FormControl = new FormControl();
  availableWorkflows: Select2OptionData[] = [];

  @ViewChild('bucketsTable', { static: false }) table: any;

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
	  this.getWorkflows();
    this.bucketsService.bucketsChange.subscribe(buckets => this.buckets = buckets);

    for (let b in this.buckets){
      this.buckets[b].triggersChange = new Observable((observer) => {
            this.buckets[b].observer = observer;
            this.bucketsService.getAllTriggers().then(triggers => this.buckets[b].observer.next(triggers));
        });
      this.buckets[b].triggersChange.subscribe(triggers => this.buckets[b].triggers = triggers);
    }
	}

  /**
	 * Based on the search filter input, filter out the buckets based on matching some parameters (name, desc.).
	 */
	get filterBuckets(): Bucket[]  {
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
		modalRef.componentInstance.title = 'Create a new Bucket';
		modalRef.componentInstance.submitText = 'Add Bucket';

    modalRef.result.then(bucket => {
			this.bucketsService.addBucket(bucket).then(() => {
				this.toastrService.success(`Added <b>${bucket.name}</b>`);
			})
		}, () => null)
	}

	editBucket(bucket: Bucket): void {
		const modalRef = this.modalService.open(BucketsModalComponent, { size: 'lg' });
		modalRef.componentInstance.existing = true;
		modalRef.componentInstance.title = 'Edit Bucket';
		modalRef.componentInstance.submitText = 'Edit Bucket';
		modalRef.componentInstance.bucket = bucket.clone();

    modalRef.result.then(bucket => {
			this.bucketsService.editBucket(bucket).then(() => {
				this.toastrService.success(`Added <b>${bucket.name}</b>`);
			})
		}, () => null)
	}

  async deleteBucket(bucketToDelete: Bucket) {
		await this.utils.confirm(`Are you sure you want to delete <b>${ bucketToDelete.name }</b>?`);
		this.bucketsService
			.deleteBucket(bucketToDelete)
			.then(() => this.toastrService.success(`Deleted <b>${ bucketToDelete.name }</b>`))
			.catch(e => this.toastrService.error(`Error deleting <b>${ e.message }</b>`));
	}

  addTrigger(bucket: Bucket): void {
		const modalRef = this.modalService.open(TriggersModalComponent, { size: 'lg' });
		modalRef.componentInstance.title = 'Create a new Trigger';
		modalRef.componentInstance.submitText = 'Add Trigger';
    modalRef.componentInstance.availableWorkflows = this.availableWorkflows;

    modalRef.result.then(trigger => {
      console.log(trigger);
			this.bucketsService.addTrigger(bucket, trigger).then(() => {
				this.toastrService.success(`Added Trigger`);
			})
		}, () => null)

  }

  editTrigger(trigger_to_edit: BucketTrigger): void {
		const modalRef = this.modalService.open(TriggersModalComponent, { size: 'lg' });
		modalRef.componentInstance.title = 'Edit a Trigger';
		modalRef.componentInstance.submitText = 'Edit Trigger';
    modalRef.componentInstance.availableWorkflows = this.availableWorkflows;

    const bucket = this.buckets.find(obj => obj.id == trigger_to_edit["parent"]);
    modalRef.result.then(trigger => {
			this.bucketsService.editTrigger(bucket, trigger, trigger_to_edit["id"]).then(() => {
				this.toastrService.success(`Added Trigger`);
			})
		}, () => null)

  }

  async deleteTrigger(trigger: BucketTrigger) {
    const bucket = this.buckets.find(obj => obj.id == trigger["parent"]);
		await this.utils.confirm(`Are you sure you want to delete <b>${ trigger.id }</b>?`);
		this.bucketsService
			.deleteTrigger(bucket, trigger)
			.then(() => this.toastrService.success(`Deleted <b>${ trigger.id }</b>`))
			.catch(e => this.toastrService.error(`Error deleting <b>${ e.message }</b>`));
	}

  toggleExpandRow(row) {
//    console.log('Toggled Expand Row!', row);
    this.table.rowDetail.toggleExpandRow(row);
  }

  onDetailToggle(event) {
//    console.log('Detail Toggled', event);
  }

  /**
	 * Grabs an array of playbooks/workflows from the server (id, name pairs).
	 * From this array, creates an array of Select2Option data with the id and playbook/workflow name.
	 */
	getWorkflows(): void {
		this.bucketsService
			.getWorkflows()
			.then(workflows => {
				workflows.forEach(workflow => {
					this.availableWorkflows.push({
						id: workflow.id,
						text: `${workflow.name}`,
					});
				});
			});
	}

	/**
	 * Converts the workflow ids array of a scheduled task into a readable string for display in the datatable.
	 * @param scheduledTask Scheduled task to convert the workflows of
	 */
	getFriendlyWorkflows(trigger: BucketTrigger): string {
		if (!this.availableWorkflows || !trigger.workflow) { return ''; }

		return this.availableWorkflows.filter(workflow => {
			return trigger.workflow;
		}).map(workflow => workflow.text).join(', ');

	}
}
