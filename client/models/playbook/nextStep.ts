import { Condition } from './condition';

export class NextStep {
	name: string;
	status: string;
	conditions: Condition[] = [];
}