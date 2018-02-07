import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Message } from '../models/message/message';
import { MessageListing } from '../models/message/messageListing';
import { Argument } from '../models/playbook/argument';

@Injectable()
export class MessagesService {
	constructor(private authHttp: JwtHttp) { }

	/**
	 * Grabs an array of message listings from the server.
	 */
	listMessages(): Promise<MessageListing[]> {
		return this.authHttp.get('/api/messages')
			.toPromise()
			.then(this.extractData)
			.then(messageListing => messageListing as MessageListing[])
			.catch(this.handleError);
	}

	/**
	 * Queries a given message by ID.
	 * @param messageId ID of message to query
	 */
	getMessage(messageId: number): Promise<Message> {
		return this.authHttp.get(`/api/messages/${messageId}`)
			.toPromise()
			.then(this.extractData)
			.then(message => message as Message)
			.catch(this.handleError);
	}

	/**
	 * Performs a given action against a given message or messages by ID.
	 * @param messageIds ID or IDs array to perform action against
	 * @param action Action to perform on the message (e.g. read, unread, delete)
	 */
	performActionOnMessages(messageIds: number | number[], action: string): Promise<void> {
		if (!Array.isArray(messageIds)) { messageIds = [messageIds]; }

		return this.authHttp.put('/api/messages', { ids: messageIds, action })
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	/**
	 * Responds to a message by calling a trigger endpoint for a given workflow's execution ID.
	 * @param execution_uid Execution ID of workflow to trigger
	 * @param action Action to send to trigger endpoint
	 */
	respondToMessage(execution_uid: string, action: string): Promise<string[]> {
		const arg = new Argument();
		arg.name = 'action';
		arg.value = action;
		const body: object = {
			execution_uids: [execution_uid],
			data_in: action,
			arguments: [arg],
		};
		return this.authHttp.put('/api/triggers/send_data', body)
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	private extractData(res: Response) {
		const body = res.json();
		return body || {};
	}

	private handleError(error: Response | any): Promise<any> {
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
