import { Condition } from './condition';
import { ExecutionElement } from './executionElement';

export class Branch extends ExecutionElement {
	id: number;
	source_id: number;
	destination_id: number;
	status: string;
	priority: number;
	conditions: Condition[] = [];
}
