import { Component } from '@angular/core';
import { FormControl } from '@angular/forms';
import * as _ from 'lodash';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import 'rxjs/add/operator/debounceTime';

import { SettingsService } from './settings.service';

import { SettingsUserModalComponent } from './settings.user.modal.component';

import { Configuration } from '../models/configuration';
import { User } from '../models/user';
import { WorkingUser } from '../models/workingUser';
import { Role } from '../models/role';

@Component({
	selector: 'settings-component',
	templateUrl: 'client/settings/settings.html',
	styleUrls: [
		'client/settings/settings.css',
	],
	providers: [SettingsService],
})
export class SettingsComponent {
	configuration: Configuration = new Configuration();
	dbTypes: string[] = ['sqlite', 'mysql', 'postgresql', 'oracle', 'mssql'];
	tlsVersions: string[] = ['1.1', '1.2', '1.3'];

	//User Data Table params
	users: User[] = [];
	displayUsers: User[] = [];
	filterQuery: FormControl = new FormControl();

	constructor(
		private settingsService: SettingsService, private modalService: NgbModal,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {
		this.toastyConfig.theme = 'bootstrap';

		this.getConfiguration();
		this.getUsers();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterUsers());
	}

	filterUsers() {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayUsers = this.users.filter((user) => {
			return user.username.toLocaleLowerCase().includes(searchFilter);
		});
	}

	// System Settings
	getConfiguration(): void {
		this.settingsService
			.getConfiguration()
			.then(configuration => Object.assign(this.configuration, configuration))
			.catch(e => this.toastyService.error(e.message));
	}

	updateConfiguration(): void {
		this.settingsService
			.updateConfiguration(this.configuration)
			.then((configuration) => {
				Object.assign(this.configuration, configuration);
				this.toastyService.success('Configuration successfully updated.');
			})
			.catch(e => this.toastyService.error(e.message));
	}

	//TODO: add a better confirm dialog
	resetConfiguration(): void {
		if (!confirm("Are you sure you want to reset the configuration? \
			Note that you'll have to save the configuration after reset to update it on the server.")) { return; }

		Object.assign(this.configuration, Configuration.getDefaultConfiguration());
	}

	getUsers(): void {
		this.settingsService
			.getUsers()
			.then(users => this.displayUsers = this.users = users)
			.catch(e => this.toastyService.error(e.message));
	}

	addUser(): void {
		const modalRef = this.modalService.open(SettingsUserModalComponent);
		modalRef.componentInstance.title = 'Add New User';
		modalRef.componentInstance.submitText = 'Add User';

		const workingUser = new WorkingUser();
		workingUser.active = true;
		modalRef.componentInstance.workingUser = workingUser;

		this._handleModalClose(modalRef);
	}

	editUser(user: User): void {
		const modalRef = this.modalService.open(SettingsUserModalComponent);
		modalRef.componentInstance.title = `Edit User: ${user.username}`;
		modalRef.componentInstance.submitText = 'Save Changes';
		modalRef.componentInstance.workingUser = User.toWorkingUser(user);

		this._handleModalClose(modalRef);
	}

	deleteUser(userToDelete: User): void {
		if (!confirm(`Are you sure you want to delete the user "${userToDelete.username}"?`)) { return; }

		this.settingsService
			.deleteUser(userToDelete.id)
			.then(() => {
				this.users = _.reject(this.users, user => user.id === userToDelete.id);

				this.filterUsers();

				this.toastyService.success(`User "${userToDelete.username}" successfully deleted.`);
			})
			.catch(e => this.toastyService.error(e.message));
	}

	getFriendlyRoles(roles: Role[]): string {
		return _.map(roles, 'name').join(', ');
	}

	getFriendlyBool(val: boolean): string {
		return val ? 'Yes' : 'No';
	}

	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => {
				//Handle modal dismiss
				if (!result || !result.user) { return; }

				//On edit, find and update the edited item
				if (result.isEdit) {
					const toUpdate = _.find(this.users, u => u.id === result.user.id);
					Object.assign(toUpdate, result.user);

					this.filterUsers();

					this.toastyService.success(`User "${result.user.username}" successfully edited.`);
				} else {
					this.users.push(result.user);

					this.filterUsers();

					this.toastyService.success(`User "${result.user.username}" successfully added.`);
				}
			},
			(error) => { if (error) { this.toastyService.error(error.message); } });
	}
}
