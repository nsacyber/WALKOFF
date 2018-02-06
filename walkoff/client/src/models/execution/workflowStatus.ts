import { ActionResult } from './actionResult';

export class WorkflowStatus {
	uid: string;
	name: string;
	started_at: Date;
	/**
	 * Date when workflow ended.
	 * TODO: figure out if we want to use this for various stopping points: awaiting data, paused, completed, aborted
	 */
	finished_at: Date;
	/**
	 * Status of the workflow.
	 * Possible values: running, awaiting_data, paused, completed, aborted
	 */
	current_action_name: string;
	status: string; 
	results: ActionResult[] = [];
}
