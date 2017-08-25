import { ScheduledTaskTrigger } from './scheduledTaskTrigger';

export class ScheduledTask {
	id: number;
	name: string;
	description: string;
	status: string; //['running', 'paused', 'stopped']
	workflows: string[];
	scheduler: ScheduledTaskTrigger = new ScheduledTaskTrigger();
}