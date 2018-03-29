export class ParameterSchema {
	type: string;

	default?: any;

	placeholder?: string;
	
	// maxLength: 10;
	// Additional JSON Schema Properties can be added (e.g. maxLength)
	[key: string]: any;
}
