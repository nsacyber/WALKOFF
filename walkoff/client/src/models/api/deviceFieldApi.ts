import { ParameterSchema } from './parameterSchema';

export class DeviceFieldApi {
	name: string;
	description: string;
	encrypted: boolean;
	required: boolean = false;
	schema: ParameterSchema;
}
