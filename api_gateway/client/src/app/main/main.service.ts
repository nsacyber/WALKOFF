import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { plainToClass } from 'class-transformer';

import { Message } from '../models/message/message';
import { MessageListing } from '../models/message/messageListing';
import { UtilitiesService } from '../utilities.service';
import { DashboardService } from '../dashboards/dashboard.service';

@Injectable()
export class MainService {
	constructor (private http: HttpClient, private utils: UtilitiesService) { }

	/**
	 * Asyncryonously returns a list of imported interface names from the server.
	 */
	getInterfaceNames(): Promise<string[]> {
		return this.http.get('/api/dashboards')
			.toPromise()
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asyncronously returns a listing of initial notifications for the initial WALKOFF page load.
	 * Should return only a subset of notifications if many unread notifications exist.
	 * Will fill up to 5 read notifications if unread notifications do not exist.
	 */
	getInitialNotifications(): Promise<MessageListing[]> {
		return this.http.get('/api/notifications')
			.toPromise()
			.then((data) => plainToClass(MessageListing, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Asyncronouly retrieves a message by ID, marks it as read, and returns the message data.
	 * @param messageId DB ID of message to retrieve
	 */
	getMessage(messageId: number): Promise<Message> {
		return this.http.get(`/api/messages/${messageId}`)
			.toPromise()
			.then((data) => plainToClass(Message, data))
			.catch(this.utils.handleResponseError);
	}

}
