import { Transform } from './transform';
import { Argument } from './argument';

export class Condition {
	uid: string;
	app: string;
	action: string;
	arguments: Argument[] = [];
	transforms: Transform[] = [];
}
