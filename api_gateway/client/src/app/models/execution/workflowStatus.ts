import { Type, Exclude } from 'class-transformer';

import { NodeStatus } from './nodeStatus';

import * as moment from 'moment';
import { NodeStatusSummary } from './nodeStatusSummary';

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

	started_at?: string;

	user: string;

	app_name: string;

	action_name: string;

	label: string;

	name: string;

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

	@Type(() => NodeStatusSummary)
	node_status?: NodeStatusSummary;

	@Type(() => NodeStatus)
	node_statuses?: NodeStatus[] = [];

	get displayAppAction() : string {
		return (this.app_name && this.action_name) ? `${ this.app_name } / ${this.action_name}` : 'N/A'
	}

	get displayLabel() : string {
		return (this.label) ? this.label : 'N/A'
	}

}
