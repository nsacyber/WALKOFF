import { Component, Input } from '@angular/core';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

import { User } from '../models/user';
 
@Component({
	selector: 'user-modal',
	templateUrl: 'client/settings/settings.user.modal.html'
})
export class SettingsUserModalComponent {
	@Input() workingUser: User;
	@Input() title: string;
	@Input() submitText: string;
}