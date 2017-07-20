import { Event } from './event'

export class Case {
	id: number;
	name: string;
	note: string;
	events: Event[];
}