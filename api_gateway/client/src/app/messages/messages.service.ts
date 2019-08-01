import { Injectable } from '@angular/core';
import { plainToClass } from 'class-transformer';
import { HttpClient } from '@angular/common/http';

import { Message } from '../models/message/message';
import { MessageListing } from '../models/message/messageListing';
import { Argument } from '../models/playbook/argument';
import { UtilitiesService } from '../utilities.service';

@Injectable()
export class MessagesService {
	constructor(private http: HttpClient, private utils: UtilitiesService) {}

	/**
	 * Grabs an array of all message listings from the server.
	 */
	getAllMessageListings(): Promise<MessageListing[]> {
		return this.utils.paginateAll<MessageListing>(this.getMessageListings.bind(this));
	}

	/**
	 * Grabs an array of message listings from the server.
	 */
	getMessageListings(page: number = 1): Promise<MessageListing[]> {
		return this.http.get(`api/messages?page=${ page }`)
			.toPromise()
			.then((data: object[]) => plainToClass(MessageListing, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Queries a given message by ID.
	 * @param messageId ID of message to query
	 */
	getMessage(messageId: number): Promise<Message> {
		return this.http.get(`api/messages/${messageId}`)
			.toPromise()
			.then((data: object) => plainToClass(Message, data))
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Performs a given action against a given message or messages by ID.
	 * @param messageIds ID or IDs array to perform action against
	 * @param action Action to perform on the message (e.g. read, unread, delete)
	 */
	performActionOnMessages(messageIds: number | number[], action: string): Promise<void> {
		if (!Array.isArray(messageIds)) { messageIds = [messageIds]; }

		return this.http.put('api/messages', { ids: messageIds, action })
			.toPromise()
			.then(() => null)
			.catch(this.utils.handleResponseError);
	}

	/**
	 * Responds to a message by calling a trigger endpoint for a given workflow's execution ID.
	 * @param workflow_execution_id Execution ID of workflow to trigger
	 * @param action Action to send to trigger endpoint
	 */
	respondToMessage(workflow_execution_id: string, action: string): Promise<string[]> {
		const arg = new Argument();
		arg.name = 'action';
		arg.value = action;
		const body: object = {
			execution_ids: [workflow_execution_id],
			data_in: action,
			arguments: [arg],
		};
		return this.http.put('api/triggers/send_data', body)
			.toPromise()
			.catch(this.utils.handleResponseError);
	}
}
