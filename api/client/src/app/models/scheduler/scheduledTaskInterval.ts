import { IScheduledTaskArgs } from './ischeduledTaskArgs';
import { Moment } from 'moment';

export class ScheduledTaskInterval implements IScheduledTaskArgs {
	//One of these is required
	weeks: number;

	days: number;

	hours: number;

	minutes: number;

	seconds: number;

	//Start date is required, end date optional
	start_date: string | Moment;

	end_date: string | Moment;

	//Timezone will most likely never be used
	timezone: string;
}
