import { Argument } from './argument';
import { GraphPosition } from './graphPosition';
import { ConditionalExpression } from './conditionalExpression';
import { ExecutionElement } from './executionElement';

export class Action extends ExecutionElement {
	// _workflow_id: number;
	name: string;
	position: GraphPosition;
	app_name: string;
	action_name: string;
	device_id?: number;
	risk?: number;
	arguments: Argument[] = [];
	// output: string;
	trigger?: ConditionalExpression;
}
