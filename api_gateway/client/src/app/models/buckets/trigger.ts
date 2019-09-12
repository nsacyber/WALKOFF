import { Type, Exclude, classToClass } from 'class-transformer';

export class BucketTrigger {
	id: number;

	suffix: string;

	prefix: string;

	event_type: string = ''; //"s3:ObjectCreated:*", "s3:ObjectRemoved:*", "s3:ObjectAccessed:*"

	workflow: string = '';

	parent: number;

	constructor(parent: number) { this.parent = parent}

	clone() {
		return classToClass(this, { ignoreDecorators: true });
	}
}
