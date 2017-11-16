import { Transform } from './transform';
import { Argument } from './argument';

export class Condition {
	uid: string;
	app_name: string;
	action_name: string;
	arguments: Argument[] = [];
	transforms: Transform[] = [];
}
