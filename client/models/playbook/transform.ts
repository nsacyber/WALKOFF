import { Argument } from './argument';

export class Transform {
	uid: string;
	app_name: string;
	action_name: string;
	arguments: Argument[] = [];
}
