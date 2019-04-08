import { Component, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { ToastrService } from 'ngx-toastr';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';

import { MessagesService } from './messages.service';
import { UtilitiesService } from '../utilities.service';

import { MessagesModalComponent } from './messages.modal.component';

import { GenericObject } from '../models/genericObject';
import { MessageListing } from '../models/message/messageListing';

@Component({
	selector: 'messages-component',
	templateUrl: './messages.html',
	styleUrls: [
		'./messages.scss',
	],
	providers: [MessagesService],
})
export class MessagesComponent implements OnInit {
	//Device Data Table params
	messages: MessageListing[] = [];
	displayMessages: MessageListing[] = [];
	messageSelectConfig: Select2Options;
	filterQuery: FormControl = new FormControl();

	selectMapping: GenericObject = {};
	messageRelativeTimes: GenericObject = {};

	constructor(
		private messagesService: MessagesService, private modalService: NgbModal,
		private toastrService: ToastrService,
		public utils: UtilitiesService,
	) {}

	/**
	 * On component init, get a list of messages to display in our datatable and bind our search filter input.
	 */
	ngOnInit(): void {

		this.listMessages();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterMessages());
	}

	/**
	 * Filters the messages displayed based upon what is entered in the search filter input.
	 * Filters based on the subject line and also recalculates the relative time of when the message was created.
	 */
	filterMessages(): void {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayMessages = this.messages.filter((message) => {
			// Update our relative time first
			this.messageRelativeTimes[message.id] = this.utils.getRelativeLocalTime(message.created_at);

			return (message.subject.toLocaleLowerCase().includes(searchFilter));
		});
	}

	/**
	 * Grabs an array of message listings from the server to display and performs the initial filter.
	 */
	listMessages(): void {
		this.messagesService.getAllMessageListings()
			.then(messages => {
				this.messages = messages;
				this.filterMessages();
			})
			.catch(e => this.toastrService.error(`Error retrieving messages: ${e.message}`));
	}

	/**
	 * Grabs a full message object from the server based upon a Message Listing and opens a message modal.
	 * 
	 * @param event JS Event fired from clicking the link
	 * @param messageListing Message Listing to open/query
	 */
	openMessage(event: any, messageListing: MessageListing): void {
		event.preventDefault();

		this.messagesService.getMessage(messageListing.id)
			.then(message => {
				messageListing.is_read = true;
				messageListing.last_read_at = this.utils.getCurrentIsoString();

				const modalRef = this.modalService.open(MessagesModalComponent);
		
				modalRef.componentInstance.message = this.utils.cloneDeep(message);
		
				this._handleModalClose(modalRef);
			})
			.catch(e => this.toastrService.error(`Error opening message: ${e.message}`));
	}

	/**
	 * After confirmation, will instruct the server to delete the message IDs that are selected.
	 * Will then remove these from our display and perform the filter action once more.
	 */
	deleteSelected(): void {
		const idsToDelete = this._getSelectedIds();

		if (!confirm(`Are you sure you want to delete ${idsToDelete.length} messages?`)) { return; }

		this.messagesService.performActionOnMessages(idsToDelete, 'delete')
			.then(() => {
				this.messages = this.messages.filter(message => idsToDelete.indexOf(message.id) === -1);

				idsToDelete.forEach(id => {
					this.selectMapping[id] = false;
				});

				this.filterMessages();
			})
			.catch(e => this.toastrService.error(`Error deleting messages: ${e.message}`));
	}

	/**
	 * Instructs the server to mark the message IDs that are selected as read.
	 * Will then mark them as read within the data table.
	 */
	markSelectedAsRead(): void {
		const idsToRead = this._getSelectedIds();

		this.messagesService.performActionOnMessages(idsToRead, 'read')
			.then(() => {
				this.messages.forEach(message => {
					if (idsToRead.indexOf(message.id) !== -1) {
						message.is_read = true;
						message.last_read_at = this.utils.getCurrentIsoString();
					}
				});
			})
			.catch(e => this.toastrService.error(`Error marking messages as read: ${e.message}`));
	}

	/**
	 * Instructs the server to mark the message IDs that are selected as unread.
	 * Will then mark them as unread within the data table.
	 */
	markSelectedAsUnread(): void {
		const idsToUnread = this._getSelectedIds();

		this.messagesService.performActionOnMessages(idsToUnread, 'unread')
			.then(() => {
				this.messages.forEach(message => {
					if (idsToUnread.indexOf(message.id) !== -1) {
						message.is_read = false;
						message.last_read_at = null;
					}
				});
			})
			.catch(e => this.toastrService.error(`Error marking messages as unread: ${e.message}`));
	}

	/**
	 * Gets an array of all IDs that are selected (checkboxes checked in the data table).
	 */
	private _getSelectedIds(): number[] {
		const ids: number[] = [];

		Object.keys(this.selectMapping).forEach(id => {
			if (this.selectMapping[id]) { ids.push(+id); }
		});

		return ids;
	}

	/**
	 * On normal message modal close, do nothing. Only show an error if something goes awry.
	 * @param modalRef Modal reference that is being closed
	 */
	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => null,
			(error) => { if (error) { this.toastrService.error(error.message); } });
	}
}
