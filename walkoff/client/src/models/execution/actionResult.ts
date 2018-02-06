import { GenericObject } from '../genericObject';

export class ActionResult {
	workflow_id: string;
	name: string;
	app_name: string;
	action_name: string;
	/**
	 * Type of action result. 'SUCCESS' or 'FAILURE'.
	 */
	type: string;
	timestamp: Date;
	input: GenericObject;
	result: any;
}
