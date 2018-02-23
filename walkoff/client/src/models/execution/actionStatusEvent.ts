import { Argument } from '../playbook/argument';
import { ActionStatus } from './actionStatus';

export class ActionStatusEvent {
	static toNewActionStatus(actionStatusEvent: ActionStatusEvent): ActionStatus {
		return {
			workflow_execution_id: actionStatusEvent.workflow_execution_id,
			workflow_id: actionStatusEvent.workflow_id,
			execution_id: actionStatusEvent.execution_id,
			action_id: actionStatusEvent.action_id,
			name: actionStatusEvent.name,
			app_name: actionStatusEvent.app_name,
			action_name: actionStatusEvent.action_name,
			status: actionStatusEvent.status,
			started_at: actionStatusEvent.timestamp,
			arguments: actionStatusEvent.arguments,
			result: actionStatusEvent.result,
		};
	}

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
}
