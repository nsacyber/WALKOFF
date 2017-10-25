import { Argument } from './argument';

export class Transform {
	uid: string;
	app: string;
	action: string;
	args: Argument[] = [];
}