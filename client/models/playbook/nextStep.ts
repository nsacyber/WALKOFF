import { Condition } from './condition';

export class NextStep {
	uid: string;
	name: string;
	status: string;
	conditions: Condition[] = [];
}