import { Argument } from './argument';
import { Widget } from './widget';
import { GraphPosition } from './graphPosition';
import { NextStep } from './nextStep';
import { Condition } from './condition';
import { ActionArgument } from '../action';

export class Step {
	uid: string;
	name: string;
	position: GraphPosition;
	next_steps: NextStep[] = [];
	action: string;
	app: string;
	device_id: number;
	risk: number;
	inputs: ActionArgument[] | Argument[] = [];
	// output: string;
	widgets: Widget[] = [];
	triggers: Condition[] = [];
}