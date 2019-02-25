import { Transform } from 'class-transformer';
import { TransformationType } from 'class-transformer/TransformOperationExecutor';

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
	@Transform((value, obj, type) => {
		switch(type) {
			case TransformationType.CLASS_TO_PLAIN:
				if (value) return value.split('.').map((v, i) => ({ name: 'selection_' + i, value: v }));
				break;
			case TransformationType.PLAIN_TO_CLASS:
				if (Array.isArray(value)) return value.map(v => v.value).join('.');
				break;
			default:
				if (value) return value;
		}
	})
	selection?: string | Array<Argument>;

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
	}
}
