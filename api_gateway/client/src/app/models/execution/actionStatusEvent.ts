import { Type } from 'class-transformer';

import { Argument } from '../playbook/argument';
import { ActionStatus } from './actionStatus';

export class ActionStatusEvent {
	workflow_execution_id: string;

	workflow_id: string;

	execution_id: string;

	action_id: string;

	name: string;

	app_name: string;

	action_name: string;

	/**
	 * Type of action result. executing, success, failure
	 */
	status: string;

	timestamp: string;

	@Type(() => Argument)
	arguments: Argument[] = [];

	result?: any;

	toNewActionStatus(): ActionStatus {
		const out = new ActionStatus();

		out.workflow_execution_id = this.workflow_execution_id;
		out.workflow_id = this.workflow_id;
		out.execution_id = this.execution_id;
		out.action_id = this.action_id;
		out.name = this.name;
		out.app_name = this.app_name;
		out.action_name = this.action_name;
		out.status = this.status;
		out.started_at = this.timestamp;
		out.arguments = this.arguments;
		out.result = this.result;

		return out;
	}
}
