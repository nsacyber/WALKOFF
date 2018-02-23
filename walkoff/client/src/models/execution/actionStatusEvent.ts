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
	arguments: Argument[] = [];
	result?: any;

	toNewActionStatus(): ActionStatus {
		return {
			workflow_execution_id: this.workflow_execution_id,
			workflow_id: this.workflow_id,
			execution_id: this.execution_id,
			action_id: this.action_id,
			name: this.name,
			app_name: this.app_name,
			action_name: this.action_name,
			status: this.status,
			started_at: this.timestamp,
			arguments: this.arguments,
			result: this.result,
		};
	}
}
