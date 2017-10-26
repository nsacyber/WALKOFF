import { ArgumentSchema } from './argumentSchema';

export class ActionApi {
	name: string;
	description: string;
	args: ArgumentSchema[];
	returns: string[];
	// Name of event in the case of a triggered action, null or whitespace to indicate no event
	event: string; 
}
