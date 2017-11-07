export class Argument {
	/**
	 * Name of the argument in question
	 */
	name: string;
	/**
	 * Serves a dual purpose: if reference is unspecified, this is the static value of the input.
	 * If reference is specified, this is an optional "path" through the referenced step's output JSON.
	 * (e.g. given an output { status: 'Success', result: 'something' },
	 * passing 'result' as the value would grab 'something' from the output JSON.
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
