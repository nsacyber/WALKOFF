export class NodeStatus {

	execution_id: string;

	combined_id: string;

	node_id: string;

	label: string;

	app_name: string;

	name: string;

	status: NodeStatuses;

	result?: any;

	started_at: string;

	completed_at?: string;

	parameters?: any;

	public format(input: any, expanded = false) {
		if (!input) return 'N/A';
		const output = (expanded) ? 
			JSON.stringify(input, null, 2) : 
			JSON.stringify(input);
		
		return (output) ? output : 'N/A'
	}
}

export enum NodeStatuses {
  AWAITING_DATA = "AWAITING_DATA",
  EXECUTING = "EXECUTING",
  SUCCESS = "SUCCESS",
  FAILURE = "FAILURE",
}
