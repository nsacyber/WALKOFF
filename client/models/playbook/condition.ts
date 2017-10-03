import { Transform } from './transform';
import { Argument } from './argument';

export class Condition {
	uid: string;
	action: string;
	args: Argument[] = [];
	transforms: Transform[] = [];
}