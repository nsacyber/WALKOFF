import { Type, Expose, Exclude } from 'class-transformer';

import { Argument } from './argument';
import { ExecutionElement } from './executionElement';
import { GraphPosition } from './graphPosition';

export class Condition extends ExecutionElement {

	@Expose({ name: 'label' })
	name: string = 'Label';

	app_name: string = 'Builtin';

	@Expose({ name: 'name' })
	action_name: string = 'Condition';

	@Type(() => GraphPosition)
	position: GraphPosition;

	@Exclude()
	@Type(() => Argument)
	arguments: Argument[] = [];

	conditional: string = '';

	get all_errors(): string[] {
		return this.errors.concat(...this.arguments.map(argument => argument.all_errors))
	}
}
