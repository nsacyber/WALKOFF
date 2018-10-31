import { Type } from 'class-transformer';

import { ParameterApi } from './parameterApi';
import { ReturnApi } from './returnApi';

export class ConditionApi {
	name: string;

	description: string;

	@Type(() => ParameterApi)
	parameters: ParameterApi[] = [];

	@Type(() => ReturnApi)
	returns: ReturnApi[] = [];

	run: string;

	data_in: string;

	deprecated: boolean;

	// tags: Tag[] = [];

	summary: string;

	// external_docs: ExternalDoc[] = [];
}
