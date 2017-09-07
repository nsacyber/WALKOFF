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

	toWorkingDevice(): WorkingDevice {
		let out = new WorkingDevice();
		out.id = this.id;
		out.name = this.name;
		out.app = this.app;
		out.type = this.type;
		out.fields = {};

		this.fields.forEach(element => {
			out.fields[element.name] = element.value;
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

	toDevice(): Device {
		let out = new Device();
		out.id = this.id;
		out.name = this.name;
		out.app = this.app;
		out.type = this.type;
		out.fields = [];

		Object.keys(this.fields).forEach(function (key) {
			out.fields.push({ name: key, value: this.fields[key] });
		});

		return out;
	}
}