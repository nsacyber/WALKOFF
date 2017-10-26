export class ArgumentSchema {
	name: string;
	type: string;
	// required: boolean;
	// default: any;
	// Additional JSON Schema Properties can be added (e.g. maxLength)
	[key: string]: any;
}