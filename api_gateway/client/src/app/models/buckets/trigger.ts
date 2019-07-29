import { Type } from 'class-transformer';

export class BucketTrigger {
	id: number;

	suffix: string;

	prefix: string;

	event_type: string; //"s3:ObjectCreated:*", "s3:ObjectRemoved:*", "s3:ObjectAccessed:*"

	workflow: string;
}
