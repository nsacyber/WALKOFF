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

	get parallel_parameter() : string {
		const argument = this.arguments.find(a => a.parallelized == true);
		return (argument) ? argument.name : null;
	}

	set parallel_parameter(name: string) {
		this.arguments.forEach(a => a.parallelized = false);
		this.arguments.find(a => a.name == name).parallelized = true;
	}
}
