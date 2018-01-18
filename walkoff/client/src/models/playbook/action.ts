import { Argument } from './argument';
// import { Widget } from './widget';
import { GraphPosition } from './graphPosition';
import { Condition } from './condition';

export class Action {
	uid: string;
	name: string;
	position: GraphPosition;
	app_name: string;
	action_name: string;
	device_id?: number;
	risk?: number;
	arguments: Argument[] = [];
	// output: string;
	// widgets: Widget[] = [];
	triggers: Condition[] = [];
}
