import { Type } from 'class-transformer';

import { Metric } from './metric';

export class ActionMetric {
	name: string;

	@Type(() => Metric)
    success_metrics: Metric = new Metric();

    @Type(() => Metric)
    error_metrics: Metric = new Metric();
}