import { Transform } from './transform';
import { Argument } from './argument';

export class Condition {
	action: string;
	args: Argument[] = [];
	transforms: Transform[] = [];
}