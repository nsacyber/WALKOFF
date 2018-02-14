import { ExecutionElement } from './executionElement';
import { Condition } from './condition';

export class ConditionalExpression extends ExecutionElement {
	operator: string;
	is_negated: boolean;
	conditions: Condition[] = [];
	child_expressions: ConditionalExpression[] = [];
}
