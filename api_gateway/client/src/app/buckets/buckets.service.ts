import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';
import { UtilitiesService } from '../utilities.service';
import { plainToClass, classToPlain } from 'class-transformer';
import { Bucket } from '../models/buckets/bucket';
import { BucketTrigger } from '../models/buckets/trigger';

import { Observable, Subscriber } from 'rxjs';
import { Workflow } from '../models/playbook/workflow';

@Injectable({
  providedIn: 'root'
})
export class BucketsService {

  bucketsChange: Observable<any>;
	observer: Subscriber<any>;

	constructor (private http: HttpClient, private utils: UtilitiesService) {
    this.bucketsChange = new Observable((observer) => {
            this.observer = observer;
            this.getAllBuckets().then(buckets => this.observer.next(buckets));
        });

	}

	getAllBuckets(): Promise<Bucket[]> {
		return this.utils.paginateAll<Bucket>(this.getBuckets.bind(this));
	}

  getAllTriggers(): Promise<Bucket[]> {
		return this.getBuckets.bind(this);
	}

	getTriggers(bucket: Bucket): Promise<BucketTrigger[]> {
		return this.http.get(`/api/buckets/${bucket.id}/triggers`)
			.toPromise()
			.then((data) => plainToClass(BucketTrigger, data))
			.catch(this.utils.handleResponseError);
	}


  emitChange(data: any) {
        if (this.observer) this.getAllBuckets().then(buckets => this.observer.next(buckets));
        return data;
    }


	getBuckets(page: number = 1): Promise<Bucket[]> {
		return this.http.get(`/api/buckets?page=${ page }`)
			.toPromise()
			.then((data) => plainToClass(Bucket, data))
			.catch(this.utils.handleResponseError);
	}

	addBucket(bucket: Bucket): Promise<Bucket> {
		return this.http.post('/api/buckets', classToPlain(bucket))
			.toPromise()
			.then((data) => this.emitChange(data))
			.then((data) => plainToClass(Bucket, data))
			.catch(this.utils.handleResponseError);
	}

	editBucket(bucket: Bucket): Promise<Bucket> {
		return this.http.put(`/api/buckets/${ bucket.id }`, classToPlain(bucket))
			.toPromise()
			.then((data) => this.emitChange(data))
			.then((data) => plainToClass(Bucket, data))
			.catch(this.utils.handleResponseError);
	}

	deleteBucket(bucket: Bucket): Promise<void> {
		return this.http.delete(`/api/buckets/${ bucket.id }`)
			.toPromise()
			.then((data) => this.emitChange(data))
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	addTrigger(bucket: Bucket, trigger: BucketTrigger): Promise<BucketTrigger> {
		return this.http.post(`/api/buckets/${ bucket.id }/triggers`, classToPlain(trigger))
			.toPromise()
			.then((data) => bucket.emitTriggerChange(this, data))
			.then((data) => plainToClass(BucketTrigger, data))
			.catch(this.utils.handleResponseError);
	}

  editTrigger(bucket: Bucket, trigger: BucketTrigger, trigger_id:number): Promise<BucketTrigger> {
    console.log(trigger);
		return this.http.put(`/api/buckets/${ bucket.id }/triggers/${ trigger_id }`, classToPlain(trigger))
			.toPromise()
			.then((data) => bucket.emitTriggerChange(this, data))
			.then((data) => plainToClass(BucketTrigger, data))
			.catch(this.utils.handleResponseError);
	}

  deleteTrigger(bucket: Bucket, trigger: BucketTrigger): Promise<void> {
		return this.http.delete(`/api/buckets/${ bucket.id }/triggers/${ trigger.id }`)
			.toPromise()
			.then((data) => bucket.emitTriggerChange(this, data))
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

  getWorkflows(): Promise<Workflow[]> {
		return this.http.get('/api/workflows')
			.toPromise()
			.then((data) => plainToClass(Workflow, data))
			.catch(this.utils.handleResponseError);
	}
}
