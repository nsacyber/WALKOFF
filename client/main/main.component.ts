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
import { Message } from '../models/message/message';

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

	constructor(
		private mainService: MainService, private authService: AuthService,
		private modalService: NgbModal, private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {
		this.toastyConfig.theme = 'bootstrap';

		this.mainService.getInterfaceNamess()
			.then(interfaceNames => this.interfaceNames = interfaceNames);

		this.updateUserInfo();
		this.getInitialNotifications();
		this.getNotificationsSSE();
	}

	getInitialNotifications(): void {
		this.mainService.getInitialNotifications()
			.then(messageListings => this.messageListings = messageListings.concat(this.messageListings))
			.catch(e => this.toastyService.error(`Error retrieving notifications: ${e.message}`));
	}

	getNotificationsSSE(): void {
		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				const eventSource = new (window as any).EventSource('/api/notifications/stream?access_token=' + authToken);

				eventSource.addEventListener('message', (message: any) => {
					const newMessage: MessageListing = JSON.parse(message.data);

					const existingMessage = this.messageListings.find(m => m.id === newMessage.id);
					const index = this.messageListings.indexOf(existingMessage);
					// If an existing message exists, replace it with the incoming message. Otherwise add it to the top of the array.
					if (index > -1) {
						this.messageListings[index] = newMessage;
					} else {
						this.messageListings.unshift(newMessage);
					}

					// Remove the oldest message that is read if we have too many (>5) read messages
					if (this.messageListings.filter(m => m.is_read).length > 5) {
						this.messageListings.pop();
					}
				});
				eventSource.addEventListener('read', (message: any) => {
					const update: MessageUpdate = JSON.parse(message.data);

					if (!this.messageModalRef || !this.messageModalRef.componentInstance) { return; }

					if (this.messageModalRef.componentInstance.message.id === update.id) {
						(this.messageModalRef.componentInstance.message as Message).read_by.push(update.username);
					}
				});
				eventSource.addEventListener('respond', (message: any) => {
					const update: MessageUpdate = JSON.parse(message.data);

					const existingMessage = this.messageListings.find(m => m.id === update.id);

					if (existingMessage) {
						existingMessage.awaiting_response = false;
					}

					if (!this.messageModalRef || !this.messageModalRef.componentInstance) { return; }

					if (this.messageModalRef.componentInstance.message.id === update.id) {
						(this.messageModalRef.componentInstance.message as Message).responded_at = update.timestamp;
						(this.messageModalRef.componentInstance.message as Message).responded_by = update.username;
						(this.messageModalRef.componentInstance.message as Message).awaiting_response = false;
					}
				});
				eventSource.addEventListener('error', (err: Error) => {
					console.error(err);
				});
			});
	}

	updateUserInfo(): void {
		const refreshToken = sessionStorage.getItem('refresh_token');
		
		const decoded = this.jwtHelper.decodeToken(refreshToken);

		this.currentUser = decoded.identity;
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

				this.messageModalRef = this.modalService.open(MessagesModalComponent);
				
				this.messageModalRef.componentInstance.message = _.cloneDeep(message);
		
				this._handleModalClose(this.messageModalRef);
			})
			.catch(e => this.toastyService.error(`Error opening message: ${e.message}`));
	}

	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => null,
			(error) => { if (error) { this.toastyService.error(error.message); } });
	}
}
