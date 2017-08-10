import { CaseEvent } from './caseEvent'

export class Case {
	id: number;
	name: string;
	note: string;
	events: Event[];
}