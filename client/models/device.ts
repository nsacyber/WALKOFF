export class Device {
	id: number;
	name: string;
	username: string;
	//Should not be populated on read, only for write
	password: string;
	ip: string;
	port: number;
	app: string;
	extra_fields: Object;
}