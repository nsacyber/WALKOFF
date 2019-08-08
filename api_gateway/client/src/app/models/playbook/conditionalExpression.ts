import { Type } from 'class-transformer';

import { ExecutionElement } from './executionElement';
import { Condition } from './condition';

export class ConditionalExpression extends ExecutionElement {
	operator: string;
	
	is_negated: boolean;

	@Type(() => Condition)
	conditions: Condition[] = [];

	@Type(() => ConditionalExpression)
	child_expressions: ConditionalExpression[] = [];

	get all_errors(): string[] {
		return this.errors
				   .concat(...this.conditions.map(condition => condition.all_errors))
				   .concat(...this.child_expressions.map(expression => expression.all_errors))
	}
}
