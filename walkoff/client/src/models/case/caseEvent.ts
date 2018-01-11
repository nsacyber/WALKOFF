import { Case } from './case';

export class CaseEvent {
	id: number;
	timestamp: Date;
	type: string;
	originator: string;
	message: string;
	note: string;
	data: object;
	cases: Case[];
}
