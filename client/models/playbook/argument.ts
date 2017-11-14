export class Argument {
	/**
	 * Name of the argument in question
	 */
	name: string;
	/**
	 * The static value of the argument in question. Only used if reference is not specified.
	 * If reference is specified, selector is used to select specific values.
	 */
	value: any;
	/**
	 * Reference to a Step UID to use the output of
	 */
	reference: string;
	/**
	 * Selector is currently specified in the UI as a string,
	 * but is split and sent/ingested as an array containing strings and numbers
	 */
	selector: string | Array<string | number>;
}
