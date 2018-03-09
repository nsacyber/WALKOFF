import { Type } from 'class-transformer';

import { CurrentAction } from './currentAction';
import { WorkflowStatus } from './workflowStatus';

export class WorkflowStatusEvent {
	execution_id: string;

	workflow_id: string;

	name: string;

	timestamp: string;

	status: string;

	@Type(() => CurrentAction)
	current_action?: CurrentAction;

	toNewWorkflowStatus(): WorkflowStatus {
		const out = new WorkflowStatus();

		out.execution_id = this.execution_id;
		out.workflow_id = this.workflow_id;
		out.name = this.name;
		out.status = this.status;
		out.current_action = this.current_action;

		return out;
	}
}
