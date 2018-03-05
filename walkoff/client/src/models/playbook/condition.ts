import { Transform } from './transform';
import { Argument } from './argument';
import { ExecutionElement } from './executionElement';

export class Condition extends ExecutionElement {
	// _action_id?: number;
	// _branch_id?: number;
	app_name: string;
	action_name: string;
	is_negated: boolean;
	arguments: Argument[] = [];
	transforms: Transform[] = [];
}
