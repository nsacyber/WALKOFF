import { Device } from './device';

export class WorkingDevice {
	static toDevice(workingDevice: WorkingDevice): Device {
		const out = new Device();
		out.id = workingDevice.id;
		out.name = workingDevice.name;
		out.description = workingDevice.description;
		out.app = workingDevice.app;
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
	app: string;
	type: string;
	fields: { [key: string]: any } = {};
}
