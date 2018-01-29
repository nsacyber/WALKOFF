import { Argument } from './argument';
import { ExecutionElement } from './executionElement';

export class Transform extends ExecutionElement {
	id: number;
	// _condition_id: number;
	app_name: string;
	action_name: string;
	arguments: Argument[] = [];
}
