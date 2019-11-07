import { Component, Input } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';

import { MainService } from './main.service';
import { UtilitiesService } from '../utilities.service';

import { WorkingUser } from '../models/workingUser';
import { User } from '../models/user';
import { AuthService } from '../auth/auth.service';

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

	changeType: string;

	constructor(
		private mainService: MainService, public activeModal: NgbActiveModal,
		private toastrService: ToastrService, private authService: AuthService) {
	}

	ngOnInit(): void {
		this.mainService.getUser(this.username)
			.then((profile) => {
				this.user = profile;
				this.editPersonalUser.old_username = profile.username;
				this.editPersonalUser.new_username = profile.username;
			})
	}

	async submit(): Promise<void> {
		const validationMessage = this.validate();
		if (validationMessage) {
			this.toastrService.error(validationMessage);
			return;
		}

		// Copy formData before sending to prevent modifying the form
		const profileData = Object.assign({}, this.editPersonalUser);
		if (this.changeType == 'username' && !profileData.password) {
			profileData.password = profileData.old_password;
		}
		if (this.changeType == 'password') {
			profileData.new_username = profileData.old_username;
		}

		try {
			// Update the user profile
			await this.mainService.updateUser(profileData);

			// If user name has changed / log the user back in
			if (profileData.old_username != profileData.new_username)
				await this.authService.login(profileData.new_username, profileData.password);

			// Close the modal
			this.activeModal.close(profileData.new_username);
		}
		catch(e) {
			this.toastrService.error(e.error ? e.error.detail : 'Current Password is incorrect.');
		}
	}

	validate(): string {
		if (!this.editPersonalUser.new_username) { return 'Username is not specified.'; }
		if (!this.editPersonalUser.old_password) { return 'You must specify a password.'; }
		if (this.passwordConfirm !== this.editPersonalUser.password) { return 'Passwords do not match.'; }

		return '';
	}
}
