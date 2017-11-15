import { Device } from './device';

export class WorkingDevice {
	static toDevice(workingDevice: WorkingDevice): Device {
		const out = new Device();
		out.id = workingDevice.id;
		out.name = workingDevice.name;
		out.description = workingDevice.description;
		out.app_name = workingDevice.app_name;
		out.type = workingDevice.type;
		out.fields = [];

		Object.keys(workingDevice.fields).forEach(function (key) {
			out.fields.push({ name: key, value: workingDevice.fields[key] });
		});

		return out;
	}

	id: number;
	name: string;
	description: string;
	app_name: string;
	type: string;
	fields: { [key: string]: any } = {};
}
