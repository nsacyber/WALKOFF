import { Transform, Exclude, Expose } from 'class-transformer';
import { TransformationType } from 'class-transformer/TransformOperationExecutor';

export enum Variant {
	STATIC_VALUE = 'STATIC_VALUE',
	ACTION_RESULT = 'ACTION_RESULT',
	WORKFLOW_VARIABLE = 'WORKFLOW_VARIABLE',
	GLOBAL = 'GLOBAL'
}

export class Argument {
	@Expose({ name: 'id_'})
	@Exclude({ toPlainOnly: true})
	id?: number;
	// _node_id: number;
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
	 * The type of argument in question
	 */
	variant: Variant = Variant.STATIC_VALUE;

	/**
	 * If the worker should run this action in parallel based on this parameter or not
	 */
	parallelized: boolean = false;

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
	@Exclude()
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
		return this.value;
	}

	sanitize(): void {
		// First trim any string inputs for sanitation and so we can check against ''
		if (typeof (this.value) === 'string') { this.value = this.value.trim(); }
	}
}
