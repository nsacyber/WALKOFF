import { CurrentAction } from './currentAction';
import { WorkflowStatus } from './workflowStatus';

export class WorkflowStatusEvent {
	execution_id: string;
	workflow_id: string;
	name: string;
	timestamp: string;
	status: string; 
	current_action?: CurrentAction;

	toNewWorkflowStatus(): WorkflowStatus {
		return {
			execution_id: this.execution_id,
			workflow_id: this.workflow_id,
			name: this.name,
			status: this.status,
			current_action: this.current_action,
		};
	}
}
