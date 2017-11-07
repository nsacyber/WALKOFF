import { Component, Input } from '@angular/core';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig, ToastOptions, ToastData } from 'ng2-toasty';

import { SettingsService } from './settings.service';

import { User } from '../models/user';
import { WorkingUser } from '../models/workingUser';

@Component({
	selector: 'user-modal',
	templateUrl: 'client/settings/settings.user.modal.html',
	styleUrls: [
		'client/settings/settings.css',
	],
	providers: [SettingsService],
})
export class SettingsUserModalComponent {
	@Input() workingUser: WorkingUser;
	@Input() title: string;
	@Input() submitText: string;

	constructor(
		private settingsService: SettingsService, private activeModal: NgbActiveModal,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig) {
		this.toastyConfig.theme = 'bootstrap';
	}

	submit(): void {
		const validationMessage = this.validate();
		if (validationMessage) {
			this.toastyService.error(validationMessage);
			return;
		}

		//If user has an ID, user already exists, call update
		if (this.workingUser.id) {
			this.settingsService
				.editUser(WorkingUser.toUser(this.workingUser))
				.then(user => this.activeModal.close({
					user,
					isEdit: true,
				}))
				.catch(e => this.toastyService.error(e.message));
		} else {
			this.settingsService
				.addUser(WorkingUser.toUser(this.workingUser))
				.then(user => this.activeModal.close({
					user,
					isEdit: false,
				}))
				.catch(e => this.toastyService.error(e.message));
		}
	}

	validate(): string {
		if (!this.workingUser) { return 'User is not specified.'; }
		if (!this.workingUser.id && !this.workingUser.newPassword) { return 'You must specify a password.'; }
		if (this.workingUser.confirmNewPassword !== this.workingUser.newPassword) { return 'Passwords do not match.'; }

		return '';
	}
}
