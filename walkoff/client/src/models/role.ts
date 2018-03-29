import { Type } from 'class-transformer';

import { Resource } from './resource';

export class Role {
	id: number;

	name?: string;

	description?: string;

	@Type(() => Resource)
	resources?: Resource[] = [];
}
