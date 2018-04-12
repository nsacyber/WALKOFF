import { Type } from 'class-transformer';

import { Argument } from './argument';
import { GraphPosition } from './graphPosition';
import { ConditionalExpression } from './conditionalExpression';
import { ExecutionElement } from './executionElement';

export class Action extends ExecutionElement {
	// _workflow_id: number;
	name: string;

	@Type(() => GraphPosition)
	position: GraphPosition;

	app_name: string;

	action_name: string;

	@Type(() => Argument)
	device_id?: Argument = new Argument();

	risk?: number;

	@Type(() => Argument)
	arguments: Argument[] = [];

	// output: string;
	
	@Type(() => ConditionalExpression)
	trigger?: ConditionalExpression;
}
