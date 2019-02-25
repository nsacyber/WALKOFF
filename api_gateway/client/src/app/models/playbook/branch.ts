import { Type } from 'class-transformer';

import { ConditionalExpression } from './conditionalExpression';
import { ExecutionElement } from './executionElement';

export class Branch extends ExecutionElement {
	source_id: string;

	destination_id: string;

	status: string;

	priority: number;
	
	@Type(() => ConditionalExpression)
	condition?: ConditionalExpression;

	get all_errors(): string[] {
		return this.errors.concat((this.condition) ? this.condition.all_errors : []);
	}
}
