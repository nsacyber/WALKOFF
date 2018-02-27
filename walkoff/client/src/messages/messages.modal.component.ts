import { Component, Input, OnInit } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import * as moment from 'moment';

import { MessagesService } from './messages.service';

import { Message } from '../models/message/message';

@Component({
	selector: 'messages-modal',
	templateUrl: './messages.modal.html',
	styleUrls: [
		'./messages.css',
	],
	providers: [MessagesService],
})
export class MessagesModalComponent implements OnInit {
	@Input() message: Message;

	constructor(
		private messagesService: MessagesService, private activeModal: NgbActiveModal,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {}

	ngOnInit(): void {
		this.toastyConfig.theme = 'bootstrap';
	}

	/**
	 * Performs a given action against a message (e.g. accept, decline).
	 * Removes the "awaiting_response" flag and updates the responded_at within the view.
	 * @param action Action to perform against the message
	 */
	performMessageAction(action: string) {
		this.messagesService.respondToMessage(this.message.workflow_execution_uid, action)
			.then(() => {
				this.message.awaiting_response = false;
				this.message.responded_at = new Date();
			})
			.catch(e => this.toastyService.error(`Error performing ${action} on message: ${e.message}`));
	}

	/**
	 * Dismisses this modal.
	 */
	dismiss(): void {
		this.activeModal.dismiss();
	}

	/**
	 * Converts a date time to a relative value (e.g. '5 minutes ago').
	 * @param time Time to convert
	 */
	getRelativeTime(time: Date): string {
		return moment(time).fromNow();
	}
}
