import { Component } from '@angular/core';
import { FormControl } from '@angular/forms';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';
import 'rxjs/add/operator/debounceTime';

import { SettingsService } from './settings.service';

import { SettingsUserModalComponent } from './settings.user.modal.component';

import { Configuration } from '../models/configuration';
import { User } from '../models/user';
import { WorkingUser } from '../models/workingUser';
import { Role } from '../models/role';
import { SettingsTimeoutModalComponent } from './settings.timeout.modal.component';
import { UtilitiesService } from '../utilities.service';

@Component({
	selector: 'settings-component',
	templateUrl: './settings.html',
	styleUrls: [
		'./settings.scss',
	],
	providers: [SettingsService],
})
export class SettingsComponent {
	configuration: Configuration = new Configuration();

	//User Data Table params
	users: User[] = [];
	displayUsers: User[] = [];
	filterQuery: FormControl = new FormControl();

	roles: Role[] = [];

	constructor(
		private settingsService: SettingsService, private modalService: NgbModal,
		private toastrService: ToastrService, private utils: UtilitiesService,
	) {

		//this.getConfiguration();
		this.getUsers();
		this.getRoles();

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
			.then(configuration => {
				Object.assign(this.configuration, configuration);
			})
			.catch(e => this.toastrService.error(e.message));
	}

	updateConfiguration(): void {
		this.settingsService
			.updateConfiguration(this.configuration)
			.then((configuration) => {
				Object.assign(this.configuration, configuration);
				this.toastrService.success('Configuration successfully updated.');
			})
			.catch(e => this.toastrService.error(e.message));
	}

	//TODO: add a better confirm dialog
	resetConfiguration(): void {
		if (!confirm("Are you sure you want to reset the configuration? \
			Note that you'll have to save the configuration after reset to update it on the server.")) { return; }

		Object.assign(this.configuration, Configuration.getDefaultConfiguration());
	}

	getRoles(): void {
		this.settingsService
			.getRoles()
			.then(roles => this.roles = roles)
			.catch(e => this.toastrService.error(`Error retrieving roles: ${e.message}`));
	}

	getUsers(): void {
		this.settingsService
			.getAllUsers()
			.then(users => this.displayUsers = this.users = users)
			.catch(e => this.toastrService.error(`Error retrieving users: ${e.message}`));
	}

	addUser(): void {
		const modalRef = this.modalService.open(SettingsUserModalComponent);
		modalRef.componentInstance.title = 'Add New User';
		modalRef.componentInstance.submitText = 'Add User';
		modalRef.componentInstance.roles = this.roles;

		const workingUser = new WorkingUser();
		workingUser.active = true;
		modalRef.componentInstance.workingUser = workingUser;

		this._handleModalClose(modalRef);
	}

	editTimeout(): void {
		const modalRef = this.modalService.open(SettingsTimeoutModalComponent);
		modalRef.componentInstance.configuration = this.configuration;
		modalRef.result.then(() => this.updateConfiguration()).catch(() => null)
	}

	editUser(user: User): void {
		const modalRef = this.modalService.open(SettingsUserModalComponent);
		modalRef.componentInstance.title = `Edit User: ${user.username}`;
		modalRef.componentInstance.submitText = 'Save Changes';
		modalRef.componentInstance.roles = this.roles;
		modalRef.componentInstance.workingUser = WorkingUser.fromUser(user);

		this._handleModalClose(modalRef);
	}

	async deleteUser(userToDelete: User) {
		await this.utils.confirm(`Are you sure you want to delete <b>${userToDelete.username}</b>?`)

		this.settingsService
			.deleteUser(userToDelete.id)
			.then(() => {
				this.users = this.users.filter(user => user.id !== userToDelete.id);

				this.filterUsers();

				this.toastrService.success(`User "${userToDelete.username}" successfully deleted.`);
			})
			.catch(e => this.toastrService.error(e.message));
	}

	getFriendlyRoles(roles: string[]): string {
		return roles.map(r => this.roles.find(role => role.id == r).name).join(', ');
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
					const toUpdate = this.users.find(u => u.id === result.user.id);
					Object.assign(toUpdate, result.user);

					this.filterUsers();

					this.toastrService.success(`User "${result.user.username}" successfully edited.`);
				} else {
					this.users.push(result.user);

					this.filterUsers();

					this.toastrService.success(`User "${result.user.username}" successfully added.`);
				}
			},
			(error) => { if (error) { this.toastrService.error(error.message); } });
	}
}
