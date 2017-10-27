import { ArgumentApi } from './argumentApi';

export class ActionApi {
	name: string;
	description: string;
	args: ArgumentApi[];
	returns: string[];
	// Name of event in the case of a triggered action, null or whitespace to indicate no event
	event: string; 
}
