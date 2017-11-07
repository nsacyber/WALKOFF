export class ParameterSchema {
	type: string;
	required: boolean = false;
	default: any;
	placeholder: string;
	// maxLength: 10;
	// Additional JSON Schema Properties can be added (e.g. maxLength)
	[key: string]: any;
}
