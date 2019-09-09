import { Type, Exclude } from 'class-transformer';

import { Argument } from '../playbook/argument';

export enum NodeStatuses {
	  //PAUSED = "PAUSED",
    AWAITING_DATA = "AWAITING_DATA",
    //PENDING = "PENDING",
    //COMPLETED = "COMPLETED",
    //ABORTED = "ABORTED",
    EXECUTING = "EXECUTING",
    SUCCESS = "SUCCESS",
    FAILURE = "FAILURE",
}

export class NodeStatus {

	execution_id: string;

	node_id: string;

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

	parameters?: any;

	@Exclude({ toPlainOnly: true })
	localized_started_at?: string;

	@Exclude({ toPlainOnly: true })
	localized_completed_at?: string;
}
