import { Type } from 'class-transformer';

import { ActionMetric } from './actionMetric';

export class AppMetric {
	name: string;

	count: string;

	@Type(() => ActionMetric)
	actions: ActionMetric[] = [];
}