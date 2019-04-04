import { Type, Exclude } from 'class-transformer';

import { ActionStatus } from './actionStatus';

import * as moment from 'moment';
import { ActionIdentification } from './actionIdentification';

export enum WorkflowStatuses {
	PAUSED = "PAUSED",
    AWAITING_DATA = "AWAITING_DATA",
    PENDING = "PENDING",
    COMPLETED = "COMPLETED",
    ABORTED = "ABORTED",
    EXECUTING = "EXECUTING",
    //SUCCESS = "SUCCESS",
    //FAILURE = "FAILURE",
} 

export class WorkflowStatus {
	
	id?: string;

	execution_id: string;

	workflow_id: string;
	
	name: string;

	started_at?: string;

	user: string;

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

	@Type(() => ActionIdentification)
	action_status?: ActionIdentification;

	@Type(() => ActionStatus)
	action_statuses?: ActionStatus[] = [];

	@Exclude({ toPlainOnly: true })
	localized_started_at?: string;

	@Exclude({ toPlainOnly: true })
	localized_completed_at?: string;

	get completed_at_local() : string {
		return moment(this.completed_at).format('LL LTS');
	}

	get completed_at_relative() : string {
		return moment(this.completed_at).fromNow();
	}

	get started_at_local() : string {
		return moment(this.started_at).format('LL LTS');
	}

	get started_at_relative() : string {
		return moment(this.started_at).fromNow();
	}
}
