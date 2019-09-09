import { Type, Expose } from 'class-transformer';

import { Argument } from '../playbook/argument';
import { NodeStatus } from './nodeStatus';

export class NodeStatusEvent {
	execution_id: string;

	@Expose({name: 'node_id'})
	node_id: string;

	label: string;

	app_name: string;

	name: string;

	result?: any;

	/**
	 * Type of action result. executing, success, failure
	 */
	status: string;

	started_at: string;

	completed_at: string

	parameters?: any;

	toNewNodeStatus(): NodeStatus {
		const out = new NodeStatus();

		out.execution_id = this.execution_id;
		out.node_id = this.node_id;
		out.name = this.name;
		out.app_name = this.app_name;
		out.label = this.label;
		out.status = this.status;
		out.started_at = this.started_at;
		out.completed_at = this.completed_at;
		out.parameters = this.parameters;
		out.result = this.result;

		return out;
	}
}
