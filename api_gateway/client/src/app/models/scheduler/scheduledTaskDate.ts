import { IScheduledTaskArgs } from './ischeduledTaskArgs';
import { Moment } from 'moment';

export class ScheduledTaskDate implements IScheduledTaskArgs {
	run_date: string | Moment;

	//Timezone will most likely never be used
	timezone: string;
}
