import { Condition } from './condition';
import { ExecutionElement } from './executionElement';

export class Branch extends ExecutionElement {
	source_id: string;
	destination_id: string;
	status: string;
	priority: number;
	conditions: Condition[] = [];
}
