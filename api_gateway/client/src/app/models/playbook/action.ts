import { Type, Expose } from 'class-transformer';

import { Argument } from './argument';
import { GraphPosition } from './graphPosition';
import { ConditionalExpression } from './conditionalExpression';
import { ExecutionElement } from './executionElement';

export class Action extends ExecutionElement {
	// _workflow_id: number;
	@Expose({ name: 'label' })
	name: string;

	@Type(() => GraphPosition)
	position: GraphPosition;

	app_name: string;

	app_version: string;

	@Expose({ name: 'name' })
	action_name: string;

	risk?: number;

	parallel_parameter?: Argument;

	@Expose({ name: 'parameters' })
	@Type(() => Argument)
	arguments: Argument[] = [];

	get all_errors(): string[] {
		return this.errors
				   .concat(...(this.arguments) ? this.arguments.map(argument => argument.all_errors) : [])
	}

	getArgument(name: string) : Argument {
		return this.arguments.find(a => a.name == name)
	}

	get parallel_parameter_name() : string {
		return (this.parallel_parameter) ? this.parallel_parameter.name : null;
	}

	set parallel_parameter_name(name: string) {
		this.parallel_parameter = this.getArgument(name);
	}
}
