import { Type, Expose } from 'class-transformer';

import { Argument } from '../playbook/argument';
import { ActionStatus } from './actionStatus';

export class ActionStatusEvent {
	execution_id: string;

	@Expose({name: 'node_id'})
	action_id: string;

	label: string;

	app_name: string;

	name: string;

	result?: any;

	/**
	 * Type of action result. executing, success, failure
	 */
	status: string;

	started_at: string;

	completed_at: string

	@Type(() => Argument)
	arguments: Argument[] = [];

	

	toNewActionStatus(): ActionStatus {
		const out = new ActionStatus();

		out.execution_id = this.execution_id;
		out.action_id = this.action_id;
		out.name = this.name;
		out.app_name = this.app_name;
		out.label = this.label;
		out.status = this.status;
		out.started_at = this.started_at;
		out.completed_at = this.completed_at;
		out.arguments = this.arguments;
		out.result = this.result;

		return out;
	}
}
