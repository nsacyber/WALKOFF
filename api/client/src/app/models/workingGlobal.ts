import { Global } from './global';
import { GenericObject } from './genericObject';

export class WorkingGlobal {
	id: number;

	name: string;

	description: string;

	app_name: string;

	type: string;

	fields: GenericObject = {};

	public static toGlobal(workingGlobal: WorkingGlobal): Global {
		const out = new Global();
		out.id = workingGlobal.id;
		out.name = workingGlobal.name;
		out.description = workingGlobal.description;
		out.app_name = workingGlobal.app_name;
		out.type = workingGlobal.type;
		out.fields = [];

		Object.keys(workingGlobal.fields).forEach(key => {
			out.fields.push({ name: key, value: workingGlobal.fields[key] });
		});

		return out;
	}

	public static fromGlobal(global: Global) : WorkingGlobal {
		const out = new WorkingGlobal();
		out.id = global.id;
		out.name = global.name;
		out.description = global.description;
		out.app_name = global.app_name;
		out.type = global.type;
		out.fields = {};

		global.fields.forEach(element => {
			out.fields[element.name] = element.value !== undefined ? element.value : null;
		});

		return out;
	}
}
