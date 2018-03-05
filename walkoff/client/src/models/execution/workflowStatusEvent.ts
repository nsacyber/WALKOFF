import { CurrentAction } from './currentAction';
import { WorkflowStatus } from './workflowStatus';

export class WorkflowStatusEvent {
	static toNewWorkflowStatus(workflowStatusEvent: WorkflowStatusEvent): WorkflowStatus {
		return {
			execution_id: workflowStatusEvent.execution_id,
			workflow_id: workflowStatusEvent.workflow_id,
			name: workflowStatusEvent.name,
			status: workflowStatusEvent.status,
			current_action: workflowStatusEvent.current_action,
		};
	}

	execution_id: string;
	workflow_id: string;
	name: string;
	timestamp: string;
	status: string; 
	current_action?: CurrentAction;
}
