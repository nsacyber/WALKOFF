import { Component } from '@angular/core';
import _ from 'lodash';
import { NgbModal, NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';

import { SettingsService } from './settings.service';

import { SettingsUserModalComponent } from './settings.user.modal.component';

import { Configuration } from '../models/configuration';
import { User, WorkingUser } from '../models/user';
import { Role } from '../models/role';

@Component({
	selector: 'settings-component',
	templateUrl: 'client/settings/settings.html',
	styleUrls: [
		'client/settings/settings.css',
	],
	providers: [SettingsService]
})
export class SettingsComponent {
	configuration: Configuration = new Configuration();
	dbTypes: string[] = ['sqlite', 'mysql', 'postgresql', 'oracle', 'mssql'];
	tlsVersions: string[] = ['1.1', '1.2', '1.3'];

	//User Data Table params
	users: User[];
	filterQuery: string = "";
	rowsOnPage: number = 10;
	sortBy: string = "username";
	sortOrder: string = "asc";

	//User modal params
	userModalTitle: string;
	userModalSubmitText: string;
	workingUser: User;

	constructor(private settingsService: SettingsService, private modalService: NgbModal) {
		this.getConfiguration();
		this.getUsers();
	}

	// System Settings
	getConfiguration(): void {
		this.settingsService
			.getConfiguration()
			.then(configuration => _.assign(this.configuration, configuration))
			.catch(e => console.log(e));
	}

	updateConfiguration(): void {
		this.settingsService
			.updateConfiguration(this.configuration)
			.then(configuration => _.assign(this.configuration, configuration))
			.catch(e => console.log(e));
	}

	//TODO: add a better confirm dialog
	resetConfiguration(): void {
		if (!confirm("Are you sure you want to reset the configuration? Note that you'll have to save the configuration after reset to update it on the server.")) return; 

		_.assign(this.configuration, Configuration.getDefaultConfiguration());

		console.log(this.configuration);
	}

	//User Settings
	getUsers(): void {
		this.settingsService
			.getUsers()
			.then(users => this.users = users)
			.catch(e => console.log(e));
	}

	addUser(): void {
		const modalRef = this.modalService.open(SettingsUserModalComponent);
		modalRef.componentInstance.title = 'Add New User';
		modalRef.componentInstance.submitText = 'Add User';
		modalRef.componentInstance.workingUser = new WorkingUser();
	}

	editUser(user: User): void {
		const modalRef = this.modalService.open(SettingsUserModalComponent);
		modalRef.componentInstance.title = `Edit User: ${user.username}`;
		modalRef.componentInstance.submitText = 'Save Changes';
		modalRef.componentInstance.workingUser = User.toWorkingUser(user);
	}

	addUserOrSaveChanges(user: User): void {
		//If user has an ID, user already exists, call update
		if (user.id) {
			this.settingsService
				.editUser(user)
				.then((user) => {
					let toUpdate = _.find(this.users, u => u.id === user.id);
					_.assign(toUpdate, user);
				})
				.catch(e => console.log(e));
		}
		else {
			this.settingsService
				.addUser(user)
				.then(user => this.users.push(user))
				.catch(e => console.log(e));
		}
	}

	deleteUser(userName: string): void {
		if (!confirm(`Are you sure you want to delete the user "${userName}"?`)) return; 

		this.settingsService
			.deleteUser(userName)
			.then(() => this.users = _.reject(this.users, user => user.username === userName))
			.catch(e => console.log(e));
	}

	getFriendlyRoles(roles: Role[]): string {
		return _.map(roles, 'name').join(', ');
	}

	getFriendlyBool(boolean: boolean): string {
		return boolean ? 'Yes' : 'No';
	}
}


// @Component({
//   	selector: 'user-modal',
// 	templateUrl: 'client/settings/settings.user.modal.html',
// 	// styleUrls: [
// 	// 	'client/settings/settings.user.modal.css',
// 	// ],
// 	providers: [SettingsService]
// })
// export class UserModalComponent {
// 	public visible = false;
// 	public visibleAnimate = false;

// 	public show(): void {
// 		this.visible = true;
// 		setTimeout(() => this.visibleAnimate = true, 100);
// 	}

// 	public hide(): void {
// 		this.visibleAnimate = false;
// 		setTimeout(() => this.visible = false, 300);
// 	}

// 	public validate(): void {
		
// 	}

// 	public onContainerClicked(event: MouseEvent): void {
// 		if ((<HTMLElement>event.target).classList.contains('modal')) {
// 		this.hide();
// 		}
// 	}
// }