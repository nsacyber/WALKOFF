import { IScheduledTaskArgs } from './ischeduledTaskArgs';

export class ScheduledTaskDate implements IScheduledTaskArgs {
	run_date: Date;
	//Timezone will most likely never be used
	timezone: string;
}