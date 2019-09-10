import { Type } from 'class-transformer';

import { WorkflowStatus } from './workflowStatus';
import { NodeStatusSummary } from './nodeStatusSummary';

export class WorkflowStatusEvent {
	execution_id: string;

	workflow_id: string;

	name: string;

	app_name: string;

	label: string;

	user: string;

	started_at: string;

	completed_at: string;

	status: string;

	@Type(() => NodeStatusSummary)
	node_status?: NodeStatusSummary;

	toNewWorkflowStatus(): WorkflowStatus {
		const out = new WorkflowStatus();

		out.execution_id = this.execution_id;
		out.workflow_id = this.workflow_id;
		out.name = this.name;
		out.app_name = this.app_name;
		out.user = this.user;
		out.label = this.label
		out.status = this.status;
		out.node_status = this.node_status;
		out.started_at = this.started_at;
		out.completed_at = this.completed_at;
		return out;
	}
}
