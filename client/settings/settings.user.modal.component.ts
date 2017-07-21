import { Component, Input } from '@angular/core';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

import { SettingsService } from './settings.service';

import { WorkingUser, User } from '../models/user';
 
@Component({
	selector: 'user-modal',
	templateUrl: 'client/settings/settings.user.modal.html',
	styleUrls: [
		'client/settings/settings.css'
	],
	providers: [SettingsService]
})
export class SettingsUserModalComponent {
	@Input() workingUser: WorkingUser;
	@Input() title: string;
	@Input() submitText: string;

	constructor(private settingsService: SettingsService, private activeModal: NgbActiveModal) { }

	submit(): void {
		let validationMessage = this.validate();
		if (validationMessage) {
			console.error(validationMessage);
			return;
		}

		//If user has an ID, user already exists, call update
		if (this.workingUser.id) {
			this.settingsService
				.editUser(WorkingUser.toUser(this.workingUser))
				.then(user => this.activeModal.close({
					user: user,
					isEdit: true
				}))
				.catch(e => console.log(e));
		}
		else {
			this.settingsService
				.addUser(WorkingUser.toUser(this.workingUser))
				.then(user => this.activeModal.close({
					user: user,
					isEdit: false
				}))
				.catch(e => console.log(e));
		}
	}

	validate(): string {
		if (!this.workingUser) return 'User is not specified.';
		if (this.workingUser.id && this.workingUser.newPassword && this.workingUser.confirmNewPassword !== this.workingUser.newPassword) return 'Passwords do not match.';

		return '';
	}
}