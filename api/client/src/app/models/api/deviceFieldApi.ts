import { Type } from 'class-transformer';

import { ParameterSchema } from './parameterSchema';

export class DeviceFieldApi {
	name: string;

	description?: string;

	encrypted?: boolean;

	required?: boolean = false;

	@Type(() => ParameterSchema)
	schema: ParameterSchema;
}
