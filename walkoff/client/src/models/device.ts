import { WorkingDevice } from './workingDevice';

export class Device {
	id: number;

	name: string;

	description: string;

	type: string;

	app_name: string;

	fields: Array<{ name: string; value: any }> = [];

	toWorkingDevice(): WorkingDevice {
		const out = new WorkingDevice();
		out.id = this.id;
		out.name = this.name;
		out.description = this.description;
		out.app_name = this.app_name;
		out.type = this.type;
		out.fields = {};

		this.fields.forEach(element => {
			out.fields[element.name] = element.value !== undefined ? element.value : null;
		});

		return out;
	}
}
