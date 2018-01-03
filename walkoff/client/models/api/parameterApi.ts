import { ParameterSchema } from './parameterSchema';

export class ParameterApi {
	name: string;
	description: string;
	example: any;
	required: boolean = false;
	schema: ParameterSchema;
}
