import { Component, Input } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import * as moment from 'moment';

import { MessagesService } from './messages.service';

import { Message } from '../models/message';

@Component({
	selector: 'messages-modal',
	templateUrl: 'client/messages/messages.modal.html',
	styleUrls: [
		'client/messages/messages.css',
	],
	providers: [MessagesService],
})
export class MessagesModalComponent {
	@Input() message: Message;


	constructor(
		private messagesService: MessagesService, private activeModal: NgbActiveModal,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {
		this.toastyConfig.theme = 'bootstrap';
	}

	performMessageAction(action: string) {
		this.messagesService.performMessageAction(this.message.workflow_execution_uid, action)
			.then(() => {
				this.message.awaiting_response = false;
				this.message.responded_at = new Date();
			})
			.catch(e => this.toastyService.error(`Error performing ${action} on message: ${e.message}`));
	}

	dismiss(): void {
		this.activeModal.dismiss();
	}

	getRelativeTime(time: Date): string {
		return moment(time).fromNow();
	}
}
