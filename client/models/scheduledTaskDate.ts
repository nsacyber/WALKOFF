import { IScheduledTaskTrigger } from './ischeduledTaskTrigger';

export class ScheduledTaskDate implements IScheduledTaskTrigger {
	run_time: Date;
	//Timezone will most likely never be used
	timezone: string;
}