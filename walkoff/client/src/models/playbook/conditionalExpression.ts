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
}
