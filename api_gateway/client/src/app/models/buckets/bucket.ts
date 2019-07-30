import { Type } from 'class-transformer';
import { Injectable } from '@angular/core';
import { Expose, classToClass, Exclude } from 'class-transformer';
import { HttpClient } from '@angular/common/http';
import { UtilitiesService } from '../../utilities.service';
import 'rxjs/add/operator/toPromise';
import { Observable, Subscriber } from 'rxjs';

import { BucketTrigger } from './trigger';
import { BucketsService } from '../../buckets/buckets.service';
import { plainToClass, classToPlain } from 'class-transformer';

@Injectable({
  providedIn: 'root',
})
export class Bucket {
	id: number;

	name: string;

	description: string;

  triggersChange: Observable<any>;
  observer: Subscriber<any>;

  @Type(() => BucketTrigger)
  triggers: BucketTrigger[] = []

	@Exclude()
	isHidden: boolean = true;

  clone() {
      return classToClass(this, { ignoreDecorators: true });
  }

  constructor () {
	}


  emitTriggerChange(bucketService: BucketsService, data: any) {
        if (this.observer) bucketService.getAllTriggers().then(triggers => this.observer.next(triggers));
        return data;
    }

}

