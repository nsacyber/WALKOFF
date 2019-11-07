import { Type, Expose } from 'class-transformer';

import { Resource } from './resource';

export class Role {

	@Expose({ name: "id_" })
	id: string;

	name?: string;

	description?: string;

	@Type(() => Resource)
	resources?: Resource[] = [];
}
