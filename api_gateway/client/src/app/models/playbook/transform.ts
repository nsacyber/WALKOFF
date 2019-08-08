import { Type, Expose, Exclude } from 'class-transformer';

import { Argument } from './argument';
import { ExecutionElement } from './executionElement';
import { GraphPosition } from './graphPosition';
import { ActionType } from '../api/actionApi';
import { WorkflowNode } from './WorkflowNode';

export class Transform extends ExecutionElement implements WorkflowNode {
	
	@Exclude()
    action_type: ActionType = ActionType.TRANSFORM;

	@Expose({ name: 'label' })
	name: string = 'Label';

	app_name: string = 'Builtin';

	app_version: string;

	@Expose({ name: 'name' })
	action_name: string = 'Transform';

	@Type(() => GraphPosition)
	position: GraphPosition;

	@Exclude()
	@Type(() => Argument)
	arguments: Argument[] = [];

	transform: string = '';

	get all_errors(): string[] {
		return this.errors.concat(...this.arguments.map(argument => argument.all_errors))
	}
}
