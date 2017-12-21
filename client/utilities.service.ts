import { Injectable } from '@angular/core';
import * as moment from 'moment';

@Injectable()
export class UtilitiesService {
	/**
	 * Returns a truncated input sting based on the length inputted.
	 * Will simply return input if input length is less than or equal the length of the specified length.
	 * @param input String to truncate, if applicable
	 * @param length Length of truncated string (not including the ellipsis appended)
	 * @param def Default value to use if the string is null of whitespace
	 */
	getTruncatedString(input: string, length: number, def?: string): string {
		input = this.getDefaultString(input, def);
		if (input.length <= length) { return input; }
		return input.substr(0, length) + '...';
	}

	/**
	 * Returns a trimmed and defaulted (if empty) string.
	 * @param input String to return trimmed or defaulted
	 * @param def Default value to use if the string is null of whitespace
	 */
	getDefaultString(input: string, def?: string) {
		if (!input) { input = ''; }
		const trimmed = input.trim();
		if (!trimmed) {
			if (def) { return def; }
			return '';
		}
		return trimmed;
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
