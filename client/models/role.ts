import { Resource } from './resource';

export class Role {
	role_id: number;
	name: string;
	description: string;
	resources: Resource[] = [];
}
