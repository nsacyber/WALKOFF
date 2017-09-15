export class DeviceType {
	name: string;
	description: string;
	app: string;
	fields: IDeviceTypeField[] = [];
}

export interface IDeviceTypeField {
	name: string;
	type: string;
	[key: string]: any;
}