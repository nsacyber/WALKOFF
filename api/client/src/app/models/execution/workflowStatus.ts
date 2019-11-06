import { Type } from 'class-transformer';
import { NodeStatus } from './nodeStatus';

export class WorkflowStatus {

	execution_id: string;

	workflow_id: string;

	started_at?: string;

	user: string;

	app_name: string;

	action_name: string;

	label: string;

	name: string;

	completed_at?: string;

	status: WorkflowStatuses;

	@Type(() => NodeStatus)
	node_statuses?: NodeStatus[] = [];

	get displayAppAction() : string {
		return (this.app_name && this.action_name) ? `${ this.app_name } / ${this.action_name}` : 'N/A'
	}

	get displayLabel() : string {
		return (this.label) ? this.label : 'N/A'
	}

}

export enum WorkflowStatuses {
	PAUSED = "PAUSED",
    AWAITING_DATA = "AWAITING_DATA",
    PENDING = "PENDING",
    COMPLETED = "COMPLETED",
    ABORTED = "ABORTED",
    EXECUTING = "EXECUTING",
}
