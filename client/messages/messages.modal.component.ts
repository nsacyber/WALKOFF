import { Component, Input } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';

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
				this.message.awaiting_action = false;
				this.message.acted_on_at = new Date();
			})
			.catch(e => this.toastyService.error(`Error performing ${action} on message: ${e.message}`));
	}

	dismiss(): void {
		this.activeModal.dismiss();
	}
}
