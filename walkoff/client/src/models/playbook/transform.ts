import { Type } from 'class-transformer';

import { Argument } from './argument';
import { ExecutionElement } from './executionElement';

export class Transform extends ExecutionElement {
	// _condition_id: number;

	app_name: string;

	action_name: string;

	@Type(() => Argument)
	arguments: Argument[] = [];

	get all_errors(): string[] {
		return this.errors.concat(...this.arguments.map(argument => argument.all_errors))
	}
}
