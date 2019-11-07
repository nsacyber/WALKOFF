import { WalkoffEvent } from "./walkoffEvent";

export class BuildStatusEvent implements WalkoffEvent {
    build_id: string;
    
    build_status: string;
	
	stream: string;

	get channels() : string[] {
		return ['all', this.build_id];
	}
}
