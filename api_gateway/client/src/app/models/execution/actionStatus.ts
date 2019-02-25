import { Type, Exclude } from 'class-transformer';

import { Argument } from '../playbook/argument';

export class ActionStatus {
	workflow_execution_id: string;

	workflow_id: string;

	execution_id: string;

	action_id: string;

	name: string;

	app_name: string;

	action_name: string;

	/**
	 * Type of action result. executing, success, failure
	 */
	status: string;

	started_at: string;

	completed_at?: string;

	@Type(() => Argument)
	arguments: Argument[] = [];

	result?: any;

	@Exclude({ toPlainOnly: true })
	localized_started_at?: string;

	@Exclude({ toPlainOnly: true })
	localized_completed_at?: string;
}
