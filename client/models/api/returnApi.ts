
import { ParameterSchema } from './parameterSchema';

export class ReturnApi {
	status: string;
	failure: boolean = false;
	description: string;
	schema: ParameterSchema;
	examples: any;
}
