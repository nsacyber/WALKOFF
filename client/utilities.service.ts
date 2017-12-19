import { Injectable } from '@angular/core';
import * as moment from 'moment';

@Injectable()
export class UtilitiesService {
	/**
	 * Returns a truncated input sting based on the length inputted.
	 * Will simply return input if input length is less than or equal the length of the specified length.
	 * @param input String to truncate, if applicable
	 * @param length Length of truncated string (not including the ellipsis appended)
	 */
	getTruncatedString(input: string, length: number): string {
		if (input.length <= length) { return input; }
		return input.substr(0, length) + '...';
	}

	/**
	 * Gets a locale string for a given UTC datetime object or string.
	 * @param time Inputted date object or string representation of a UTC time
	 */
	getLocalTime(time: Date | string): string {
		return moment.utc(time).local().toLocaleString();
	}
	
	/**
	 * Gets a relative time string for a given UTC datetime object or string (e.g. 5 hours ago).
	 * @param time Inputted date object or string representation of a UTC time
	 */
	getRelativeLocalTime(time: Date | string): string {
		return moment.utc(time).local().fromNow();
	}
}
