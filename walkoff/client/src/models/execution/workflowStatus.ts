import { Type, Exclude } from 'class-transformer';

import { ActionStatus } from './actionStatus';
import { CurrentAction } from './currentAction';

export class WorkflowStatus {
	execution_id: string;

	workflow_id: string;
	
	name: string;

	started_at?: string;

	/**
	 * Date when workflow ended.
	 * TODO: figure out if we want to use this for various stopping points: awaiting data, paused, completed, aborted
	 */
	completed_at?: string;

	/**
	 * Status of the workflow.
	 * Possible values: queued, running, awaiting_data, paused, completed, aborted
	 */
	status: string; 

	@Type(() => CurrentAction)
	current_action?: CurrentAction;

	@Type(() => ActionStatus)
	action_statuses?: ActionStatus[] = [];

	@Exclude({ toPlainOnly: true })
	localized_started_at?: string;

	@Exclude({ toPlainOnly: true })
	localized_completed_at?: string;
}
