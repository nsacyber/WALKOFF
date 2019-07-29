import { Type } from 'class-transformer';

import { BucketTrigger } from './trigger';

export class Bucket {
	id: number;

	name: string;

	description: string;

	@Type(() => BucketTrigger)
	bucket_trigger: BucketTrigger[] = [];
}
