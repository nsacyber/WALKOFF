import { Component, Input } from '@angular/core';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

import { WorkingUser } from '../models/user';
 
@Component({
	selector: 'user-modal',
	templateUrl: 'client/settings/settings.user.modal.html',
	styleUrls: [
		'client/settings/settings.css'
	]
})
export class SettingsUserModalComponent {
	@Input() workingUser: WorkingUser;
	@Input() title: string;
	@Input() submitText: string;

	constructor(private activeModal: NgbActiveModal) { }

	submit(): void {
		if (!this.validate()) return;
		// this.onSubmit.emit(workingUser);
		this.activeModal.close(this.workingUser);
	}

	validate(): boolean {
		if (!this.workingUser) return false;
		if (this.workingUser.id && this.workingUser.newPassword && this.workingUser.confirmNewPassword !== this.workingUser.newPassword) return false;

		return true;
	}
}