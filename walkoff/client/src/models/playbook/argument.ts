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
	errors?: string[] = [];

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

	hasInput() : boolean {
		return this.reference || this.value;
	}

	sanitize(): void {
		// Delete errors
		delete this.errors;

		// First trim any string inputs for sanitation and so we can check against ''
		if (typeof (this.value) === 'string') { this.value = this.value.trim(); }

		// Additionally, remove "value" if reference is specified
		if (this.reference && this.value !== undefined) {
			delete this.value;
		}

		// Remove reference if unspecified
		if (this.reference === '') { delete this.reference; }

		// If nothing specified set value to empty array
		if (!this.value && !this.reference) {
			return;
		}

		// Split our string argument selector into what the server expects
		if (!this.reference) {
			delete this.selection;
			return;
		}

		if (this.selection == null) {
			this.selection = [];
		} else if (typeof (this.selection) === 'string') {
			this.selection = this.selection.trim();
			this.selection = this.selection.split('.');

			if (this.selection[0] === '') {
				this.selection = [];
			} else {
				// For each value, if it's a valid number, convert it to a number.
				for (let i = 0; i < this.selection.length; i++) {
					if (!isNaN(this.selection[i] as number)) { this.selection[i] = +this.selection[i]; }
				}
			}
		}
	}
}
