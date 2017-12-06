// import { Permission } from './permission';

export class Resource {
	resource_id: number;
	role_id: number;
	type: string;
	app_name: string;
	permissions: string[] = [];
	// permissions: Permission[];
}
