import { Type } from 'class-transformer';

import { Argument } from './argument';
import { ExecutionElement } from './executionElement';

export class Transform extends ExecutionElement {
	// _condition_id: number;

	app_name: string;

	action_name: string;

	@Type(() => Argument)
	arguments: Argument[] = [];
}
