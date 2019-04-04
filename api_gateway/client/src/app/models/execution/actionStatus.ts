import { Type, Exclude } from 'class-transformer';

import { Argument } from '../playbook/argument';

export enum ActionStatuses {
	//PAUSED = "PAUSED",
    AWAITING_DATA = "AWAITING_DATA",
    //PENDING = "PENDING",
    //COMPLETED = "COMPLETED",
    //ABORTED = "ABORTED",
    EXECUTING = "EXECUTING",
    SUCCESS = "SUCCESS",
    FAILURE = "FAILURE",
} 

export class ActionStatus {

	execution_id: string;

	action_id: string;

	label: string;

	app_name: string;

	name: string;

	/**
	 * Type of action result. executing, success, failure
	 */
	status: string;

	result?: any;

	started_at: string;

	completed_at?: string;

	@Type(() => Argument)
	arguments: Argument[] = [];

	@Exclude({ toPlainOnly: true })
	localized_started_at?: string;

	@Exclude({ toPlainOnly: true })
	localized_completed_at?: string;
}
