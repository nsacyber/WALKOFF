import { Argument } from './argument';

export class Transform {
	id: number;
	// _condition_id: number;
	app_name: string;
	action_name: string;
	arguments: Argument[] = [];
}
