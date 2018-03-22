import { Type } from 'class-transformer';

import { Case } from './case';

export class CaseEvent {
	id: number;

	timestamp: string;

	type: string;

	originator: string;

	message: string;

	note: string;

	data: object;

	@Type(() => Case)
	cases: Case[];
}
