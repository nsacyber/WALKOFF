
export class Device {
	id: number;

	name: string;

	description: string;

	type: string;

	app_name: string;

	fields: Array<{ name: string; value: any }> = [];
}
