import { Action } from './action';
import { Branch } from './branch';
import { ExecutionElement } from './executionElement';

export class Workflow extends ExecutionElement {
	/**
	 * UUID of the workflow.
	 */
	id: number;

	// _playbook_id: number;

	/**
	 * Name of the workflow. Updated by passing in new_name in POST.
	 */
	name: string;
	/**
	 * Array of actions specified in the workflow.
	 */
	actions: Action[] = [];
	/**
	 * Array of branches between actions.
	 */
	branches: Branch[] = [];
	/**
	 * DB ID of the action designated as the start action.
	 */
	start: number;
	/**
	 * A factor of how often the workflow fails.
	 */
	accumulated_risk: number;
}
