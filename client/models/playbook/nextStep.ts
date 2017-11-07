import { Condition } from './condition';

export class NextStep {
	uid: string;
	source_uid: string;
	destination_uid: string;
	status: string;
	priority: number;
	conditions: Condition[] = [];
}
