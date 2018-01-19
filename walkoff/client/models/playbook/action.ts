import { Argument } from './argument';
import { GraphPosition } from './graphPosition';
import { Condition } from './condition';

export class Action {
	id: number;
	// _workflow_id: number;
	name: string;
	position: GraphPosition;
	app_name: string;
	action_name: string;
	device_id: number;
	risk: number;
	arguments: Argument[] = [];
	// output: string;
	triggers: Condition[] = [];
}
