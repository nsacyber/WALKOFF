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
	@Input() messages: Message[];

	constructor(
		private messagesService: MessagesService, private activeModal: NgbActiveModal,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {
		this.toastyConfig.theme = 'bootstrap';
	}
}
