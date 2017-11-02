import { UUID } from 'angular2-uuid';

import { Step } from './step';
import { NextStep } from './nextStep';

export class Workflow {
	uid: string = UUID.UUID();
	name: string;
	steps: Step[] = [];
	next_steps: NextStep[] = [];
	// Start is UID and not step name
	start: string;
	accumulated_risk: number;
}