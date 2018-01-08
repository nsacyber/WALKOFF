import { Component } from '@angular/core';
import { JwtHelper } from 'angular2-jwt';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';

import { MessagesModalComponent } from '../messages/messages.modal.component';

import { MainService } from './main.service';
import { AuthService } from '../auth/auth.service';
import { UtilitiesService } from '../utilities.service';

import { MessageUpdate } from '../models/message/messageUpdate';
import { MessageListing } from '../models/message/messageListing';
// import { Message } from '../models/message/message';
import { GenericObject } from '../models/genericObject';

const MAX_READ_MESSAGES = 5;
const MAX_TOTAL_MESSAGES = 20;

@Component({
	selector: 'main-component',
	templateUrl: 'client/main/main.html',
	styleUrls: [
		'client/main/main.css',
	],
	providers: [MainService, AuthService, UtilitiesService],
})
export class MainComponent {
	utils = new UtilitiesService();
	currentUser: string;
	interfaceNames: string[] = [];
	jwtHelper: JwtHelper = new JwtHelper();
	messageListings: MessageListing[] = [];
	messageModalRef: NgbModalRef;
	newMessagesCount: number = 0;
	notificationRelativeTimes: GenericObject = {};

	constructor(
		private mainService: MainService, private authService: AuthService,
		private modalService: NgbModal, private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {}

	ngOnInit(): void {
		this.toastyConfig.theme = 'bootstrap';

		this.currentUser = this.authService.getAndDecodeAccessToken().user_claims.username;
		this.getInterfaceNames();
		this.getInitialNotifications();
		this.getNotificationsSSE();
	}

	getInterfaceNames(): void {
		this.mainService.getInterfaceNames()
			.then(interfaceNames => this.interfaceNames = interfaceNames)
			.catch(e => this.toastyService.error(`Error retrieving interfaces: ${e.message}`));
	}

	getInitialNotifications(): void {
		this.mainService.getInitialNotifications()
			.then(messageListings => {
				this.messageListings = messageListings.concat(this.messageListings);
				this._recalculateNewMessagesCount();
			})
			.catch(e => this.toastyService.error(`Error retrieving notifications: ${e.message}`));
	}

	getNotificationsSSE(): void {
		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				const eventSource = new (window as any).EventSource('/api/notifications/stream?access_token=' + authToken);

				eventSource.addEventListener('created', (message: any) => {
					const newMessage: MessageListing = JSON.parse(message.data);

					const existingMessage = this.messageListings.find(m => m.id === newMessage.id);
					const index = this.messageListings.indexOf(existingMessage);
					// If an existing message exists, replace it with the incoming message. Otherwise add it to the top of the array.
					if (index > -1) {
						this.messageListings[index] = newMessage;
					} else {
						this.messageListings.unshift(newMessage);
					}

					// Remove the oldest message that is read if we have too many (>5) read messages or too many total (>20)
					if (this.messageListings.filter(m => m.is_read).length > MAX_READ_MESSAGES || 
						this.messageListings.length > MAX_TOTAL_MESSAGES) {
						this.messageListings.pop();
					}

					this._recalculateNewMessagesCount();
					this.recalculateRelativeTimes();
				});
				// TODO: re-enable this if we can figure out why componentInstance is throwing an error on get
				// eventSource.addEventListener('read', (message: any) => {
				// 	const update: MessageUpdate = JSON.parse(message.data);

				// 	if (!this.messageModalRef || !this.messageModalRef.componentInstance) { return; }

				// 	if (this.messageModalRef.componentInstance.message.id === update.id) {
				// 		(this.messageModalRef.componentInstance.message as Message).read_by.push(update.username);
				// 	}
				// });
				eventSource.addEventListener('respond', (message: any) => {
					const update: MessageUpdate = JSON.parse(message.data);

					const existingMessage = this.messageListings.find(m => m.id === update.id);

					if (existingMessage) {
						existingMessage.awaiting_response = false;
					}

					// TODO: re-enable this if we can figure out why componentInstance is throwing an error on get
					// if (!this.messageModalRef || !this.messageModalRef.componentInstance) { return; }

					// if (this.messageModalRef.componentInstance.message.id === update.id) {
					// 	(this.messageModalRef.componentInstance.message as Message).responded_at = update.timestamp;
					// 	(this.messageModalRef.componentInstance.message as Message).responded_by = update.username;
					// 	(this.messageModalRef.componentInstance.message as Message).awaiting_response = false;
					// }
				});
				eventSource.addEventListener('error', (err: Error) => {
					console.error(err);
				});
			});
	}

	logout(): void {
		this.authService.logout()
			.then(() => location.href = '/login')
			.catch(e => console.error(e));
	}

	openMessage(event: any, messageListing: MessageListing): void {
		event.preventDefault();

		this.mainService.getMessage(messageListing.id)
			.then(message => {
				messageListing.is_read = true;
				messageListing.last_read_at = new Date();
				this._recalculateNewMessagesCount();

				this.messageModalRef = this.modalService.open(MessagesModalComponent);
				
				this.messageModalRef.componentInstance.message = _.cloneDeep(message);
		
				this._handleModalClose(this.messageModalRef);
			})
			.catch(e => this.toastyService.error(`Error opening message: ${e.message}`));
	}

	recalculateRelativeTimes(): void {
		this.messageListings.forEach(ml => {
			this.notificationRelativeTimes[ml.id] = this.utils.getRelativeLocalTime(ml.created_at);
		});
	}

	private _recalculateNewMessagesCount(): void {
		this.newMessagesCount = this.messageListings.filter(m => !m.is_read).length;
	}

	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => null,
			(error) => { if (error) { this.toastyService.error(error.message); } });
	}
}
