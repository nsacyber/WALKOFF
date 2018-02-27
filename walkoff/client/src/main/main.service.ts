import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Message } from '../models/message/message';
import { MessageListing } from '../models/message/messageListing';

@Injectable()
export class MainService {
	constructor (private authHttp: JwtHttp) { }

	/**
	 * Asyncryonously returns a list of imported interface names from the server.
	 */
	getInterfaceNames(): Promise<string[]> {
		return this.authHttp.get('/api/interfaces')
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	/**
	 * Asyncronously returns a listing of initial notifications for the initial WALKOFF page load.
	 * Should return only a subset of notifications if many unread notifications exist.
	 * Will fill up to 5 read notifications if unread notifications do not exist.
	 */
	getInitialNotifications(): Promise<MessageListing[]> {
		return this.authHttp.get('/api/notifications')
			.toPromise()
			.then(this.extractData)
			.then(messageListing => messageListing as MessageListing[])
			.catch(this.handleError);
	}

	/**
	 * Asyncronouly retrieves a message by ID, marks it as read, and returns the message data.
	 * @param messageId DB ID of message to retrieve
	 */
	getMessage(messageId: number): Promise<Message> {
		return this.authHttp.get(`/api/messages/${messageId}`)
			.toPromise()
			.then(this.extractData)
			.then(message => message as Message)
			.catch(this.handleError);
	}
	
	private extractData (res: Response) {
		const body = res.json();
		return body || {};
	}

	private handleError (error: Response | any): Promise<any> {
		let errMsg: string;
		let err: string;
		if (error instanceof Response) {
			const body = error.json() || '';
			err = body.error || body.detail || JSON.stringify(body);
			errMsg = `${error.status} - ${error.statusText || ''} ${err}`;
		} else {
			err = errMsg = error.message ? error.message : error.toString();
		}
		console.error(errMsg);
		throw new Error(err);
	}
}
