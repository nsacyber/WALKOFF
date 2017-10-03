import { Argument } from './argument';
import { Widget } from './widget';
import { GraphPosition } from './graphPosition';
import { NextStep } from './nextStep';

export class Step {
	uid: string;
	name: string;
	action: string;
	app: string;
	device_id: number;
	risk: number;
	input: Argument[] = [];
	// output: string;
	widgets: Widget[] = [];
	position: GraphPosition;
	next: NextStep[] = [];
}