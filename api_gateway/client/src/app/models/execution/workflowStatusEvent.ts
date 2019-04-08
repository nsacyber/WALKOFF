import { Type } from 'class-transformer';

import { WorkflowStatus } from './workflowStatus';
import { NodeStatusSummary } from './nodeStatusSummary';

export class WorkflowStatusEvent {
	execution_id: string;

	workflow_id: string;

	name: string;

	user: string;

	timestamp: string;

	status: string;

	@Type(() => NodeStatusSummary)
	node_status?: NodeStatusSummary;

	toNewWorkflowStatus(): WorkflowStatus {
		const out = new WorkflowStatus();

		out.execution_id = this.execution_id;
		out.workflow_id = this.workflow_id;
		out.name = this.name;
		out.status = this.status;
		out.node_status = this.node_status;

		return out;
	}
}
