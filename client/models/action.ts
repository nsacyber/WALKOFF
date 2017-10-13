export class Action {
	description: string;
	args: ActionArgument[];
	returns: string[];
	// Name of event in the case of a triggered action, null or whitespace to indicate no event
	event: string; 
}

export class ActionArgument {
	name: string;
	type: string;
	required: boolean;
	default: any;
}