export class Argument {
	id?: number;
	// _action_id: number;
	// _condition_id: number;
	// _transform_id: number;

	/**
	 * Name of the argument in question
	 */
	name: string;

	/**
	 * The static value of the argument in question. Only used if reference is not specified.
	 * If reference is specified, selection is used to select specific values.
	 */
	value?: any;

	/**
	 * Reference to an Action ID to use the output of
	 */
	reference?: string;
	
	/**
	 * Selection is currently specified in the UI as a string,
	 * but is split and sent/ingested as an array containing strings and numbers
	 */
	selection?: string | Array<string | number>;

	/**
	 * Array of errors returned from the server for this Argument
	 */
	errors: string[] = [];

	/**
	 * Array of errors returned from the server for this Argument and any of its descendants 
	 */
	get all_errors(): string[] {
		return this.errors;
	}
	
	/**
	 * Returns true if this Argument or any of its descendants contain errors
	 */
	get has_errors(): boolean {
		return (this.all_errors.length > 0) ? true : false;
	}
}
