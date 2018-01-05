import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Message } from '../models/message/message';
import { MessageListing } from '../models/message/messageListing';
import { Argument } from '../models/playbook/argument';

@Injectable()
export class MessagesService {
	constructor(private authHttp: JwtHttp) { }

	listMessages(): Promise<MessageListing[]> {
		return this.authHttp.get('/api/messages')
			.toPromise()
			.then(this.extractData)
			.then(messageListing => messageListing as MessageListing[])
			.catch(this.handleError);
	}

	getMessage(messageId: number): Promise<Message> {
		return this.authHttp.get(`/api/messages/${messageId}`)
			.toPromise()
			.then(this.extractData)
			.then(message => message as Message)
			.catch(this.handleError);
	}

	deleteMessages(messageIds: number | number[]): Promise<void> {
		if (!Array.isArray(messageIds)) { messageIds = [messageIds]; }

		return this.authHttp.post('/api/messages/delete', { ids: messageIds })
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	readMessages(messageIds: number | number[]): Promise<void> {
		if (!Array.isArray(messageIds)) { messageIds = [messageIds]; }

		return this.authHttp.post('/api/messages/read', { ids: messageIds })
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	unreadMessages(messageIds: number | number[]): Promise<void> {
		if (!Array.isArray(messageIds)) { messageIds = [messageIds]; }

		return this.authHttp.post('/api/messages/unread', { ids: messageIds })
			.toPromise()
			.then(() => null)
			.catch(this.handleError);
	}

	performMessageAction(execution_uid: string, action: string): Promise<string[]> {
		const arg = new Argument();
		arg.name = 'action';
		arg.value = action;
		const body: object = {
			execution_uids: [execution_uid],
			data_in: action,
			arguments: [arg],
		};
		return this.authHttp.post('/api/triggers/send_data', body)
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
