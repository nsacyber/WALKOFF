import { UUID } from 'angular2-uuid';

import { Action } from './action';
import { Branch } from './branch';

export class Workflow {
	/**
	 * UUID of the workflow.
	 */
	uid: string = UUID.UUID();
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
	 * UUID of the action designated as the start action.
	 */
	start: string;
	/**
	 * A factor of how often the workflow fails.
	 */
	accumulated_risk?: number;
}
