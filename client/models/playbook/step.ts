import { Argument } from './argument';
// import { Widget } from './widget';
import { GraphPosition } from './graphPosition';
import { Condition } from './condition';

export class Step {
	uid: string;
	name: string;
	position: GraphPosition;
	// next_steps: NextStep[] = [];
	action: string;
	app: string;
	device_id: number;
	risk: number;
	inputs: Argument[] = [];
	// output: string;
	// widgets: Widget[] = [];
	triggers: Condition[] = [];
}
