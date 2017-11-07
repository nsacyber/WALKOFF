import { GenericObject } from '../genericObject';

export class WorkflowResult {
	/**
	 * UUID of the given step execution, unique for all individual executions of this step.
	 */
	uid: string;
	/**
	 * UUID of the given step that is executing as stored in the workflow.
	 */
	step_uid: string;
	/**
	 * Name of the step to be executed as it is stored in the workflow.
	 */
	name: string;
	timestamp: string;
	/**
	 * Type of result. "SUCCESS" or "ERROR"
	 */
	type: string;
	input: GenericObject;
	result: GenericObject;
}
