import { Condition } from './condition';

export class Branch {
	id: number;
	source_id: number;
	destination_id: number;
	status: string;
	priority: number;
	conditions: Condition[] = [];
}
