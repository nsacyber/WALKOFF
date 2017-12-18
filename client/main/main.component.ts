import { Component } from '@angular/core';
import { JwtHelper } from 'angular2-jwt';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';

import { MessagesModalComponent } from '../messages/messages.modal.component';

import { MainService } from './main.service';
import { AuthService } from '../auth/auth.service';
import { UtilitiesService } from '../utilities.service';

import { Message } from '../models/message';

@Component({
	selector: 'main-component',
	templateUrl: 'client/main/main.html',
	styleUrls: [
		'client/main/main.css',
	],
	providers: [MainService, AuthService, UtilitiesService],
})
export class MainComponent {
	utilitiesService = new UtilitiesService();
	currentUser: string;
	interfaceNames: string[] = [];
	jwtHelper: JwtHelper = new JwtHelper();
	messages: Message[] = [];

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
			.then(messages => this.messages = messages.concat(this.messages))
			.catch(e => this.toastyService.error(`Error retrieving notifications: ${e.message}`));
	}

	getNotificationsSSE(): void {
		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				const eventSource = new (window as any).EventSource('/api/notifications/stream?access_token=' + authToken);

				eventSource.addEventListener('message', (message: any) => {
					const newMessage: Message = JSON.parse(message.data);

					const existingMessage = this.messages.find(m => m.id === newMessage.id);
					const index = this.messages.indexOf(existingMessage);
					// If an existing message exists, replace it with the incoming message. Otherwise add it to the top of the array.
					if (index > -1) {
						this.messages[index] = newMessage;
					} else {
						this.messages.unshift(newMessage);
					}

					// Remove the oldest message that is read if we have too many (>5) read messages
					if (this.messages.filter(m => m.is_read).length > 5) {
						this.messages.pop();
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

	// TODO: call the read endpoint before opening the message
	openMessage(event: any, message: Message): void {
		event.preventDefault();

		message.is_read = true;
		message.last_read_at = new Date();

		const modalRef = this.modalService.open(MessagesModalComponent);

		modalRef.componentInstance.message = _.cloneDeep(message);

		this._handleModalClose(modalRef);
	}

	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => null,
			(error) => { if (error) { this.toastyService.error(error.message); } });
	}
}
