import { Injectable } from '@angular/core';
import { HttpErrorResponse } from '@angular/common/http';
import * as moment from 'moment';
import * as io from 'socket.io-client';

@Injectable({
	providedIn: 'root'
})
export class UtilitiesService {
	reconnect_failed: boolean = false;

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

	extractResponseData (res: any) {
		const body = res;
		return body || {};
	}

	async handleResponseError (error: HttpErrorResponse | any): Promise<any> {
		console.log(error);

		let errMsg: string;
		let err: string;
		// if (error instanceof HttpErrorResponse && error.status == 401) {
		// 	location.href = 'login';
		// }
		// else 
		if (error instanceof HttpErrorResponse) {
			err = error.error || error.message || JSON.stringify(error);
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

	confirm(message: string, options: any = {}) : Promise<boolean> {
		return new Promise((resolve) => {
			const defaults = {
				message,
				backdrop: true,
				className: "mt-5 pt-5",
				callback: (result) => { if(result || options.alwaysResolve) resolve(result) } 
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

	readUploadedFileAsText(inputFile: File): Promise<string> {
		const temporaryFileReader = new FileReader();
	  
		return new Promise((resolve, reject) => {
		  temporaryFileReader.onerror = () => {
			temporaryFileReader.abort();
			reject(new DOMException("Problem parsing input file."));
		  };
	  
		  temporaryFileReader.onload = () => {
			resolve(temporaryFileReader.result as string);
		  };
		  temporaryFileReader.readAsText(inputFile);
		});
	}

	createSocket(namespace: string, channel: string = 'all'): SocketIOClient.Socket {
		console.log('socket', namespace, channel);
		const socket =  io(namespace, {
			query: { channel },
			reconnectionAttempts: 5,
			forceNew: true,
			path: '/walkoff/sockets/socket.io'
		});

		socket.on('reconnect_failed', () => {
			if (this.reconnect_failed) return;
			const options = {backdrop: undefined, closeButton: false, buttons: { ok: { label: 'Reload Page' }}}
			this.alert('The server stopped responding. Reload the page to try again.', options)
				.then(() => location.reload(true))
			this.reconnect_failed = true;
		})
		return socket;
	}
}
