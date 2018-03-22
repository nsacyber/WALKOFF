import { Device } from './device';
import { GenericObject } from './genericObject';

export class WorkingDevice {
	id: number;

	name: string;

	description: string;

	app_name: string;

	type: string;

	fields: GenericObject = {};

	toDevice(): Device {
		const out = new Device();
		out.id = this.id;
		out.name = this.name;
		out.description = this.description;
		out.app_name = this.app_name;
		out.type = this.type;
		out.fields = [];

		Object.keys(this.fields).forEach(key => {
			out.fields.push({ name: key, value: this.fields[key] });
		});

		return out;
	}
}
