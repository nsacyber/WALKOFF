import { WalkoffEvent } from "./walkoffEvent";

export class ConsoleEvent implements WalkoffEvent {
	execution_id: string;

	workflow_id: string;
	
	message: string;

	get channels() : string[] {
		return ['all', this.execution_id, this.workflow_id];
	}
}
