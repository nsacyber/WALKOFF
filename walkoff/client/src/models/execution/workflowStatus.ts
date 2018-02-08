import { ActionStatus } from './actionStatus';

export class WorkflowStatus {
	execution_id: string;
	workflow_id: string;
	name: string;
	started_at?: Date;
	/**
	 * Date when workflow ended.
	 * TODO: figure out if we want to use this for various stopping points: awaiting data, paused, completed, aborted
	 */
	completed_at?: Date;
	/**
	 * Status of the workflow.
	 * Possible values: queued, running, awaiting_data, paused, completed, aborted
	 */
	status: string; 
	current_action_execution_id?: string;
	current_action_id?: string;
	current_action_name?: string;
	current_app_name?: string;
	action_statuses?: ActionStatus[] = [];
}
