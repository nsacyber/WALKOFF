import { Component, Input } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';

import { MessagesService } from './messages.service';

import { Message } from '../models/message';

@Component({
	selector: 'settings-role-modal',
	templateUrl: 'client/settings/settings.roles.modal.html',
	styleUrls: [
		'client/settings/settings.css',
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
