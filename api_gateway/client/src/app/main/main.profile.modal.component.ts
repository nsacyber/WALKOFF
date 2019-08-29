import { Component, Input } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';

import { MainService } from './main.service';
import { UtilitiesService } from '../utilities.service';

import { WorkingUser } from '../models/workingUser';
import { User } from '../models/user';

@Component({
	selector: 'main-profile',
	templateUrl: './main.profile.modal.html',
	styleUrls: [
		'./main.scss',
	],
	providers: [MainService, UtilitiesService]
})

export class MainProfileModalComponent {
	@Input() username: string;
	@Input() submitText: string;

	user: User;

	editPersonalUser = {
		old_username: '',
		new_username: '',
		old_password: '',
		password: ''	
	}

	passwordConfirm :string = '';


	constructor(
		private mainService: MainService, public activeModal: NgbActiveModal,
		private toastrService: ToastrService, ) {
	}

	ngOnInit(): void {
		this.mainService.getUser(this.username)
			.then((profile) => {
				this.user = profile;
				this.editPersonalUser.old_username = profile.username;
				this.editPersonalUser.new_username = profile.username;
			})
	}



	submit(): void {
		const validationMessage = this.validate();
		if (validationMessage) {
			this.toastrService.error(validationMessage);
			return;
		}

		if (!this.editPersonalUser.password) {
			this.editPersonalUser.password = this.editPersonalUser.old_password;
		}

		this.mainService
			.updateUser(this.editPersonalUser)
			.then(user => this.activeModal.close(user))
			.catch(e => this.toastrService.error(e.error.detail));
	}

	validate(): string {
		if (!this.editPersonalUser.new_username) { return 'Username is not specified.'; }
		if (!this.editPersonalUser.old_password) { return 'You must specify a password.'; }
		if (this.passwordConfirm !== this.editPersonalUser.password) { return 'Passwords do not match.'; }

		return '';
	}
}
