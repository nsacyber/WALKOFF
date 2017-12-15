import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Message } from '../models/message';
import { Argument } from '../models/playbook/argument';

@Injectable()
export class MessagesService {
	constructor(private authHttp: JwtHttp) { }

	getMessages(): Promise<Message[]> {
		const testData: Message[] = [
			{
				id: 42,
				workflow_execution_uid: 'some-UID-here',
				workflow_name: 'MyWorkflow',
				requires_reauthorization: true,
				subject: 'Act now for huge savings! Sysadmins hate him! Find out how he tricked them with this one weird trick!',
				created_at: new Date(),
				is_read: false,
				last_read_at: null as Date,
				read_by: ['username1', 'username2'],
				awaiting_action: false,
				body: [
					{ type: 'text', data: { text: 'The walkoff did a thing. I need you to fill out some more information' } },
					{ type: 'accept_decline', data: {} },
					{ type: 'url', data: { url: 'https://go.somewhere.com', title: 'Go Here' } },
				],
			},
			{
				id: 43,
				workflow_execution_uid: 'some-other-UID-here',
				workflow_name: 'Blahblahblah',
				requires_reauthorization: false,
				subject: 'A shorter subject',
				created_at: new Date(2017, 11, 10),
				is_read: false,
				last_read_at: null as Date,
				read_by: ['arglebargle', 'morpmorp'],
				awaiting_action: true,
				body: [
					{ type: 'text', data: { text: `There is immense joy in just watching - watching all the little creatures in nature. Let's have a happy little tree in here. When you buy that first tube of paint it gives you an artist license.` } },
					{ type: 'text', data: { text: `You gotta think like a tree. It is a lot of fun. Let's put some happy little clouds in our world. Every time you practice, you learn more.` } },
					{ type: 'text', data: { text: `We don't make mistakes we just have happy little accidents. There's nothing wrong with having a tree as a friend. You need the dark in order to show the light. Be so very light. Be a gentle whisper. Of course he's a happy little stone, cause we don't have any other kind.` } },
					{ type: 'accept_decline', data: {} },
					{ type: 'url', data: { url: 'https://www.google.com' } },
				],
			},
		];

		return Promise.resolve(testData);

		return this.authHttp.get('/api/messages')
			.toPromise()
			.then(this.extractData)
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
			workflow_execution_uids: [execution_uid],
			data_in: '',
			inputs: [arg],
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
