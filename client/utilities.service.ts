import { Injectable } from '@angular/core';
import * as moment from 'moment';

@Injectable()
export class UtilitiesService {
	// tslint:disable-next-line:no-empty
	constructor() { }

	getTruncatedString(input: string, length: number): string {
		if (input.length <= length) { return input; }
		return input.substr(0, length) + '...';
	}
	
	getRelativeTime(time: Date): string {
		return moment(time).fromNow();
	}
}
