import { Type } from 'class-transformer';

import { ParameterApi } from './parameterApi';
import { ReturnApi } from './returnApi';

export class ActionApi {
	name: string;

	description: string;

	@Type(() => ParameterApi)
	parameters: ParameterApi[] = [];

	default_return: string;

	@Type(() => ReturnApi)
	returns: ReturnApi[] = [];

	// Name of event in the case of a triggered action, null or whitespace to indicate no event
	event: string;

	run: string;

	deprecated: boolean;

	// tags: Tag[] = [];

	summary: string;

	// external_docs: ExternalDoc[] = [];

	global: boolean;
}
