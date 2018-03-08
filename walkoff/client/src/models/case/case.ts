import { Type } from 'class-transformer';

import { Subscription } from './subscription';

export class Case {
	id: number;

	name: string;

	note: string;

	@Type(() => Subscription)
	subscriptions: Subscription[] = [];
}
