import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import 'rxjs/add/operator/map';
import 'rxjs/add/operator/toPromise';
import { plainToClass } from 'class-transformer';
import { UtilitiesService } from '../utilities.service';

import { Bucket } from '../models/buckets/bucket';

@Injectable()
export class BucketsService {
	constructor (private http: HttpClient, private utils: UtilitiesService) {}

	getAllBuckets(): Promise<Bucket[]> {
		return this.utils.paginateAll<Bucket>(this.getBuckets.bind(this));
	}

	getBuckets(page: number = 1): Promise<Bucket[]> {
		return this.http.get(`/api/buckets?page=${ page }`)
			.toPromise()
			.then((data: object[]) => plainToClass(Bucket, data))
			.catch(this.utils.handleResponseError);
	}

	addBucket(bucket: Bucket): Promise<Bucket> {
		return this.http.post('/api/buckets', bucket)
			.toPromise()
			.then((data: object) => plainToClass(Bucket, data))
			.catch(this.utils.handleResponseError);
	}
}
