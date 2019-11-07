import { WalkoffEvent } from "./walkoffEvent";

export class NodeStatusEvent implements WalkoffEvent {
	execution_id: string;

	combined_id: string;

	node_id: string;

	label: string;

	app_name: string;

	name: string;

	result?: any;

	status: NodeStatuses;

	started_at: string;

	completed_at: string

	parameters?: any;

	get channels() : string[] {
		return ['all', this.execution_id, this.node_id];
	}
}

export enum NodeStatuses {
	AWAITING_DATA = "AWAITING_DATA",
	EXECUTING = "EXECUTING",
	SUCCESS = "SUCCESS",
	FAILURE = "FAILURE",
}  
