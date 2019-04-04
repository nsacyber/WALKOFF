import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import * as moment from 'moment';

@Injectable({
	providedIn: 'root'
})
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
	 * Gets the current datetime as an ISO string
	 */
	getCurrentIsoString(): string {
		return moment.utc().toISOString();
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

	/**
	 * Clones JSON into a new value.
	 * @param val Value to clone
	 */
	cloneDeep<T>(val: T): T {
		return JSON.parse(JSON.stringify(val));
	}

	paginateAll<T>(serviceCall: (p: number) => Promise<T[]>, page: number = 1, allResults : T[] = []): Promise<T[]> {
		return serviceCall(page).then(results => {
			if (results.length > 0) return this.paginateAll(serviceCall, page + 1, allResults.concat(results));
			else return allResults;
		})
	}

	extractResponseData (res: Response) {
		const body = res.json();
		return body || {};
	}

	handleResponseError (error: Response | any): Promise<any> {
		let errMsg: string;
		let err: string;
		if (error instanceof Response) {
			const body = error.json() || '';
			err = body.error || body.detail || JSON.stringify(body);
			errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
		} else {
			err = errMsg = error.message ? error.message : error.toString();
		}
		// console.error(errMsg);
		throw new Error(err);
	}

	alert(message: string, options: {} = {}) : Promise<boolean> {
		return new Promise((resolve) => {
			const defaults = {
				message,
				backdrop: true,
				className: "mt-5 pt-5",
				callback: () => { resolve() } 
			}
			bootbox.alert(Object.assign({}, defaults, options));
		})
	}

	confirm(message: string, options: {} = {}) : Promise<boolean> {
		return new Promise((resolve) => {
			const defaults = {
				message,
				backdrop: true,
				className: "mt-5 pt-5",
				callback: (result) => { if(result) resolve(result) } 
			}
			bootbox.confirm(Object.assign({}, defaults, options));
		})
	}

	prompt(title: string, options: {} = {}) : Promise<any> {
		return new Promise((resolve) => {
			const defaults = {
				title,
				backdrop: true,
				className: "mt-5 pt-5",
				callback: (result) => { if(result) resolve(result) } 
			}
			bootbox.prompt(Object.assign({}, defaults, options));
		})
	}
}
