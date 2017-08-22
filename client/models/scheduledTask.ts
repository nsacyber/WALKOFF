import { IScheduledTaskTrigger } from './ischeduledTaskTrigger';

export class ScheduledTask {
	id: number;
	name: string;
	description: string;
	type: string; //['date', 'interval', 'cron']
	enabled: boolean;
	args: IScheduledTaskTrigger;
	workflows: string[];
}