import { Injectable } from '@angular/core';
import { Response } from '@angular/http';
import { JwtHttp } from 'angular2-jwt-refresh';

import { Message } from '../models/message/message';
import { MessageListing } from '../models/message/messageListing';

@Injectable()
export class MainService {
	constructor (private authHttp: JwtHttp) { }

	getInterfaceNamess(): Promise<string[]> {
		return this.authHttp.get('/api/interfaces')
			.toPromise()
			.then(this.extractData)
			.catch(this.handleError);
	}

	getInitialNotifications(): Promise<MessageListing[]> {
		return this.authHttp.get('/api/notifications')
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
