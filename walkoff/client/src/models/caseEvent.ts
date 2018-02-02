import { Case } from './case';

export class CaseEvent {
	id: number;
	timestamp: Date;
	type: string;
	ancestry: string[];
	message: string;
	note: string;
	data: object;
	cases: Case[];
}
