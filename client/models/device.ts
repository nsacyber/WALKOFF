export class Device {
	id: number;
	name: string;
	description: string;
	type: string;
	app: string;
	fields: { name: string; value: any }[] = [];
	//Below should be removed
	username: string;
	password: string;
	ip: string;
	port: number;
	extra_fields: Object;

	static toWorkingDevice(device: Device): WorkingDevice {
		let out = new WorkingDevice();
		out.id = device.id;
		out.name = device.name;
		out.description = device.description;
		out.app = device.app;
		out.type = device.type;
		out.fields = {};

		device.fields.forEach(element => {
			out.fields[element.name] = element.value !== undefined ? element.value : null;
		});

		return out;
	}
}

export class WorkingDevice {
	id: number;
	name: string;
	description: string;
	app: string;
	type: string;
	fields: { [key: string]: any } = {};

	static toDevice(workingDevice: WorkingDevice): Device {
		let out = new Device();
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
}