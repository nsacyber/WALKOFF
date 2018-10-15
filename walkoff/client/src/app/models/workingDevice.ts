import { Device } from './device';
import { GenericObject } from './genericObject';

export class WorkingDevice {
	id: number;

	name: string;

	description: string;

	app_name: string;

	type: string;

	fields: GenericObject = {};

	public static toDevice(workingDevice: WorkingDevice): Device {
		const out = new Device();
		out.id = workingDevice.id;
		out.name = workingDevice.name;
		out.description = workingDevice.description;
		out.app_name = workingDevice.app_name;
		out.type = workingDevice.type;
		out.fields = [];

		Object.keys(workingDevice.fields).forEach(key => {
			out.fields.push({ name: key, value: workingDevice.fields[key] });
		});

		return out;
	}

	public static fromDevice(device: Device) : WorkingDevice {
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
}
