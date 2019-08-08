import { Type, Exclude } from 'class-transformer';

import { ParameterApi } from './parameterApi';
import { ReturnApi } from './returnApi';

export enum ActionType {
	ACTION = 'ACTION',
	CONDITION = 'CONDITION',
	TRANSFORM = 'TRANSFORM',
	TRIGGER = 'TRIGGER'
}

export class ActionApi {
	name: string;

	description: string;

	parallel_parameter: string[];

	@Type(() => ParameterApi)
	parameters: ParameterApi[] = [];

	default_return: string;

	@Type(() => ReturnApi)
	returns: ReturnApi[] = [];

	// Name of event in the case of a triggered action, null or whitespace to indicate no event
	event: string;

	run: string;

	deprecated: boolean;

	@Exclude()
	app_name: string;

	@Exclude()
	app_version: string;

	// tags: Tag[] = [];

	summary: string;

	node_type: ActionType = ActionType.ACTION;

	// external_docs: ExternalDoc[] = [];

	global: boolean;

	get parallelParameters(): ParameterApi[] {
		return this.parameters.filter(p => p.parallelizable);
	}

	get canRunInParallel() : boolean {
		return this.parallelParameters.length > 0;
	}
}
