import { UUID } from 'angular2-uuid';

import { Step } from './step';

export class Workflow {
	uid: string = UUID.UUID();
	name: string;
	steps: Step[] = [];
	// Start is UID and not step name
	start: string;
	accumulated_risk: number;
}