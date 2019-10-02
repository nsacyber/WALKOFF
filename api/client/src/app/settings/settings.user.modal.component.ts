import { Component, Input } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';

import { SettingsService } from './settings.service';
import { UtilitiesService } from '../utilities.service';

import { WorkingUser } from '../models/workingUser';
import { Role } from '../models/role';
import { Select2OptionData } from 'ng2-select2/ng2-select2.interface';

@Component({
	selector: 'user-modal',
	templateUrl: './settings.user.modal.html',
	styleUrls: [
		'./settings.scss',
	],
	providers: [SettingsService, UtilitiesService],
})
export class SettingsUserModalComponent {
	@Input() workingUser: WorkingUser;
	@Input() title: string;
	@Input() submitText: string;
	@Input() roles: Role[];

	roleSelectData: Select2OptionData[];
	roleSelectConfig: Select2Options;
	roleSelectInitialValue: number[];

	constructor(
		private settingsService: SettingsService, public activeModal: NgbActiveModal,
		private toastrService: ToastrService, ) {
	}

	ngOnInit(): void {
		this.roleSelectData = this.roles.map((role) => {
			return { id: role.id.toString(), text: role.name };
		});

		this.roleSelectConfig = {
			width: '100%',
			placeholder: 'Select role(s)',
			multiple: true,
			allowClear: true,
			closeOnSelect: false,
		};

		if (!this.workingUser.role_ids) { this.workingUser.role_ids = []; }
		this.roleSelectInitialValue = JSON.parse(JSON.stringify(this.workingUser.role_ids));
	}

	/**
	 * Event fired on the select2 change for roles. Updates the value based on the event value.
	 * @param $event JS Event Fired
	 */
	roleSelectChange($event: any): void {
		// Convert strings to numbers here
		this.workingUser.role_ids = $event.value;//.map((id: string) => +id);
	}

	submit(): void {
		const validationMessage = this.validate();
		if (validationMessage) {
			this.toastrService.error(validationMessage);
			return;
		}

		const toSubmit = WorkingUser.toUser(this.workingUser);

		//If user has an ID, user already exists, call update
		if (toSubmit.id) {
			this.settingsService
				.editUser(toSubmit)
				.then(user => this.activeModal.close({
					user,
					isEdit: true,
				}))
				.catch(e => this.toastrService.error(e.message));
		} else {
			this.settingsService
				.addUser(toSubmit)
				.then(user => this.activeModal.close({
					user,
					isEdit: false,
				}))
				.catch(e => this.toastrService.error(e.message));
		}
	}

	validate(): string {
		if (!this.workingUser) { return 'User is not specified.'; }
		if (!this.workingUser.id && !this.workingUser.newPassword) { return 'You must specify a password.'; }
		if (this.workingUser.confirmNewPassword !== this.workingUser.newPassword) { return 'Passwords do not match.'; }

		return '';
	}
}
