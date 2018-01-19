import { Transform } from './transform';
import { Argument } from './argument';

export class Condition {
	id: number;
	// _action_id?: number;
	// _branch_id?: number;
	app_name: string;
	action_name: string;
	arguments: Argument[] = [];
	transforms: Transform[] = [];
}
