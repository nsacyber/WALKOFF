import { Type } from 'class-transformer';

import { ScheduledTaskTrigger } from './scheduledTaskTrigger';

export class ScheduledTask {
	id: number;

	name: string;

	description: string;

	status: string; //['running', 'paused', 'stopped']

	workflows: string[] = [];

	@Type(() => ScheduledTaskTrigger)
	task_trigger: ScheduledTaskTrigger = new ScheduledTaskTrigger();
}
