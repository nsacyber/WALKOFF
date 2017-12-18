import { Component } from '@angular/core';
import { FormControl } from '@angular/forms';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import * as moment from 'moment';

import { MessagesService } from './messages.service';

import { MessagesModalComponent } from './messages.modal.component';

import { GenericObject } from '../models/genericObject';
import { Message } from '../models/message';

@Component({
	selector: 'messages-component',
	templateUrl: 'client/messages/messages.html',
	styleUrls: [
		'client/messages/messages.css',
	],
	providers: [MessagesService],
})
export class MessagesComponent {
	//Device Data Table params
	messages: Message[] = [];
	displayMessages: Message[] = [];
	messageSelectConfig: Select2Options;
	filterQuery: FormControl = new FormControl();

	selectMapping: GenericObject = {};

	constructor(
		private messagesService: MessagesService, private modalService: NgbModal, 
		private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {
		this.toastyConfig.theme = 'bootstrap';

		this.getMessages();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterMessages());
	}

	filterMessages(): void {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayMessages = this.messages.filter((message) => {
			return (message.subject.toLocaleLowerCase().includes(searchFilter));
		});
	}

	getMessages(): void {
		this.messagesService.getMessages()
			.then(messages => this.displayMessages = this.messages = messages)
			.catch(e => this.toastyService.error(`Error retrieving messages: ${e.message}`));
	}

	openMessage(event: any, message: Message): void {
		event.preventDefault();

		this.messagesService.readMessages(message.id)
			.then(() => {
				message.is_read = true;
				message.last_read_at = new Date();

				const modalRef = this.modalService.open(MessagesModalComponent);
		
				modalRef.componentInstance.message = _.cloneDeep(message);
		
				this._handleModalClose(modalRef);
			})
			.catch(e => this.toastyService.error(`Error opening message: ${e.message}`));
	}

	deleteSelected(): void {
		const idsToDelete = this._getSelectedIds();

		if (!confirm(`Are you sure you want to delete ${idsToDelete.length} messages?`)) { return; }

		this.messagesService.deleteMessages(idsToDelete)
			.then(() => {
				this.messages = this.messages.filter(message => idsToDelete.indexOf(message.id) === -1);

				this.filterMessages();
			})
			.catch(e => this.toastyService.error(`Error deleting messages: ${e.message}`));
	}

	markSelectedAsRead(): void {
		const idsToRead = this._getSelectedIds();

		this.messagesService.readMessages(idsToRead)
			.then(() => {
				this.messages.forEach(message => {
					if (idsToRead.indexOf(message.id) !== -1) {
						message.is_read = true;
						message.last_read_at = new Date();
					}
				});
			})
			.catch(e => this.toastyService.error(`Error marking messages as read: ${e.message}`));
	}

	markSelectedAsUnread(): void {
		const idsToUnread = this._getSelectedIds();

		this.messagesService.unreadMessages(idsToUnread)
			.then(() => {
				this.messages.forEach(message => {
					if (idsToUnread.indexOf(message.id) !== -1) {
						message.is_read = false;
						message.last_read_at = null;
					}
				});
			})
			.catch(e => this.toastyService.error(`Error marking messages as unread: ${e.message}`));
	}

	getFriendlyTime(createdAt: Date): string {
		return moment(createdAt).fromNow();
	}

	private _getSelectedIds(): number[] {
		const ids: number[] = [];

		Object.keys(this.selectMapping).forEach(id => {
			if (this.selectMapping[id]) { ids.push(+id); }
		});

		return ids;
	}

	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => null,
			(error) => { if (error) { this.toastyService.error(error.message); } });
	}
}
