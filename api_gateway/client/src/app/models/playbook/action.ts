import { Type, Expose } from 'class-transformer';

import { Argument } from './argument';
import { GraphPosition } from './graphPosition';
import { ConditionalExpression } from './conditionalExpression';
import { ExecutionElement } from './executionElement';

export class Action extends ExecutionElement {
	// _workflow_id: number;
	@Expose({ name: 'label' })
	name: string;

	@Type(() => GraphPosition)
	position: GraphPosition;

	app_name: string;

	app_version: string;

	@Expose({ name: 'name' })
	action_name: string;

	// @Type(() => Argument)
	// global_id?: Argument = new Argument();

	risk?: number;

	@Expose({ name: 'parameters' })
	@Type(() => Argument)
	arguments: Argument[] = [];

	// output: string;
	
	@Type(() => ConditionalExpression)
	trigger?: ConditionalExpression;

	get all_errors(): string[] {
		return this.errors
				   .concat(...(this.arguments) ? this.arguments.map(argument => argument.all_errors) : [])
				   .concat((this.trigger) ? this.trigger.all_errors : [])
	}
}
