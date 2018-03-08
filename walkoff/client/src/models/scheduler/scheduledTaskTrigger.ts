import { IScheduledTaskArgs } from './ischeduledTaskArgs';

export class ScheduledTaskTrigger {
	type: string; //['date', 'interval', 'cron']

	args: IScheduledTaskArgs;
}
