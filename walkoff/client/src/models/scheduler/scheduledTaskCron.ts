import { IScheduledTaskArgs } from './ischeduledTaskArgs';
import { Moment } from 'moment';

export class ScheduledTaskCron implements IScheduledTaskArgs {
	// One of these is required
	// If specified as a string, use expression syntax described at
	// http://apscheduler.readthedocs.io/en/latest/modules/triggers/cron.html
	year: number | string; //4-digit year YYYY

	month: number | string; //1-12 month of year

	day: number | string; //1-31 day of month

	week: number | string; //1-53 week of year

	day_of_week: number | string; //1-7

	hour: number | string; //0-23 hour of day

	minute: number | string; //0-59 minute of hour

	second: number | string; //0-59 second of minute

	//Start date is required, end date optional
	start_date: string | Moment;

	end_date: string | Moment;

	//Timezone will most likely never be used
	timezone: string;
}
