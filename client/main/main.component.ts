import { Component } from '@angular/core';
import { JwtHelper } from 'angular2-jwt';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';

import { MessagesModalComponent } from '../messages/messages.modal.component';

import { MainService } from './main.service';
import { AuthService } from '../auth/auth.service';
import { Message } from '../models/message';

@Component({
	selector: 'main-component',
	templateUrl: 'client/main/main.html',
	styleUrls: [
		'client/main/main.css',
	],
	providers: [MainService, AuthService],
})
export class MainComponent {
	currentUser: string;
	interfaceNames: string[] = [];
	jwtHelper: JwtHelper = new JwtHelper();
	messages: Message[] = [
		{
			id: 43,
			workflow_execution_uid: 'some-other-UID-here',
			workflow_name: 'Blahblahblah',
			requires_reauthorization: false,
			subject: 'A shorter subject',
			created_at: new Date(2017, 11, 10),
			is_read: false,
			last_read_at: null as Date,
			read_by: ['arglebargle', 'morpmorp'],
			awaiting_action: true,
			body: [
				{ type: 'text', data: { text: `There is immense joy in just watching - watching all the little creatures in nature. Let's have a happy little tree in here. When you buy that first tube of paint it gives you an artist license.` } },
				{ type: 'text', data: { text: `You gotta think like a tree. It is a lot of fun. Let's put some happy little clouds in our world. Every time you practice, you learn more.` } },
				{ type: 'text', data: { text: `We don't make mistakes we just have happy little accidents. There's nothing wrong with having a tree as a friend. You need the dark in order to show the light. Be so very light. Be a gentle whisper. Of course he's a happy little stone, cause we don't have any other kind.` } },
				{ type: 'accept_decline', data: {} },
				{ type: 'url', data: { url: 'https://www.google.com' } },
			],
		},
		{
			id: 42,
			workflow_execution_uid: 'some-UID-here',
			workflow_name: 'MyWorkflow',
			requires_reauthorization: true,
			subject: 'Act now for huge savings! Sysadmins hate him! Find out how he tricked them with this one weird trick!',
			created_at: new Date(),
			is_read: false,
			last_read_at: null as Date,
			read_by: ['username1', 'username2'],
			awaiting_action: false,
			body: [
				{ type: 'text', data: { text: 'The walkoff did a thing. I need you to fill out some more information' } },
				{ type: 'accept_decline', data: {} },
				{ type: 'url', data: { url: 'https://go.somewhere.com', title: 'Go Here' } },
			],
		},
	];

	constructor(
		private mainService: MainService, private authService: AuthService,
		private modalService: NgbModal, private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {
		this.toastyConfig.theme = 'bootstrap';

		this.mainService.getInterfaceNamess()
			.then(interfaceNames => this.interfaceNames = interfaceNames);

		this.updateUserInfo();
		this.getNotificationsSSE();
	}

	getNotificationsSSE(): void {
		this.authService.getAccessTokenRefreshed()
			.then(authToken => {
				const eventSource = new (window as any).EventSource('/api/notifications?access_token=' + authToken);

				eventSource.addEventListener('message', (message: any) => {
					const newMessage: Message = JSON.parse(message.data);
					this.messages.push(newMessage);
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

	openMessage(event: any, message: Message): void {
		event.preventDefault();

		const modalRef = this.modalService.open(MessagesModalComponent);

		modalRef.componentInstance.message = _.cloneDeep(message);

		this._handleModalClose(modalRef);

		this.messages.splice(this.messages.indexOf(message), 1);
	}

	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => null,
			(error) => { if (error) { this.toastyService.error(error.message); } });
	}
}
