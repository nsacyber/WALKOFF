import { WorkingDevice } from './workingDevice';

export class Device {
	static toWorkingDevice(device: Device): WorkingDevice {
		const out = new WorkingDevice();
		out.id = device.id;
		out.name = device.name;
		out.description = device.description;
		out.app_name = device.app_name;
		out.type = device.type;
		out.fields = {};

		device.fields.forEach(element => {
			out.fields[element.name] = element.value !== undefined ? element.value : null;
		});

		return out;
	}

	id: number;
	name: string;
	description: string;
	type: string;
	app_name: string;
	fields: Array<{ name: string; value: any }> = [];
}
