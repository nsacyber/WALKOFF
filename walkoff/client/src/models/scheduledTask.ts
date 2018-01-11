import { ScheduledTaskTrigger } from './scheduledTaskTrigger';

export class ScheduledTask {
	id: number;
	name: string;
	description: string;
	status: string; //['running', 'paused', 'stopped']
	workflows: string[];
	task_trigger: ScheduledTaskTrigger = new ScheduledTaskTrigger();
}
