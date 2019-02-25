
import { Type } from 'class-transformer';

import { ParameterSchema } from './parameterSchema';

export class ReturnApi {
	status: string;

	failure: boolean = false;

	description: string;

	@Type(() => ParameterSchema)
	schema: ParameterSchema;

	examples: any;
}
