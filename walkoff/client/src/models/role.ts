import { Resource } from './resource';

export class Role {
	id: number;
	name?: string;
	description?: string;
	resources?: Resource[] = [];
}
