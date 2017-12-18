import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Message } from '../models/message';

@Injectable()
export class MainService {
	constructor (private authHttp: JwtHttp) { }

	getInterfaceNamess(): Promise<string[]> {
		return this.authHttp.get('/api/interfaces')
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	getInitialNotifications(): Promise<Message[]> {
		const testdata = [
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
				awaiting_response: true,
				body: [
					{ type: 'text', data: { text: `There is immense joy in just watching - watching all the little creatures in nature. Let's have a happy little tree in here. When you buy that first tube of paint it gives you an artist license.` } },
					{ type: 'text', data: { text: `You gotta think like a tree. It is a lot of fun. Let's put some happy little clouds in our world. Every time you practice, you learn more.` } },
					{ type: 'text', data: { text: `We don't make mistakes we just have happy little accidents. There's nothing wrong with having a tree as a friend. You need the dark in order to show the light. Be so very light. Be a gentle whisper. Of course he's a happy little stone, cause we don't have any other kind.` } },
					{ type: 'accept_decline', data: {} },
					{ type: 'url', data: { url: 'https://www.google.com' } },
				],
			},
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
				awaiting_response: false,
				responded_at: new Date(2017, 11, 10),
				responded_by: 'somename',
				body: [
					{ type: 'text', data: { text: 'The walkoff did a thing. I need you to fill out some more information' } },
					{ type: 'accept_decline', data: {} },
					{ type: 'url', data: { url: 'https://go.somewhere.com', title: 'Go Here' } },
				],
			},
		];

		return Promise.resolve(testdata);

		return this.authHttp.get('/api/notifications')
			.toPromise()
			.then(this.extractData)
			.then(messages => messages as Message)
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
