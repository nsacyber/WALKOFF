import { Condition } from './condition';

export class ConditionalExpression {
	id: string;
	operator: string;
	conditions: Condition[] = [];
	child_expressions: ConditionalExpression[] = [];
}
