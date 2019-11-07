import { Type } from 'class-transformer';
import { WalkoffEvent } from './walkoffEvent';
import { NodeStatusEvent } from './nodeStatusEvent';

export class WorkflowStatusEvent implements WalkoffEvent {
	execution_id: string;

	workflow_id: string;

	name: string;

	app_name: string;

	action_name: string;

	label: string;

	user: string;

	started_at: string;

	completed_at: string;

	status: WorkflowStatuses;

	@Type(() => NodeStatusEvent)
	node_statuses?: NodeStatusEvent[];

	get channels() : string[] {
		return ['all', this.execution_id, this.workflow_id];
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