import { Subscription } from './subscription';

export class Case {
	id: number;
	name: string;
	note: string;
	subscriptions: Subscription[] = [];
	events: Event[];
}
