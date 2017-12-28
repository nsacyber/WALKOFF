import { Component, ViewEncapsulation } from '@angular/core';
import { FormControl } from '@angular/forms';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import 'rxjs/add/operator/debounceTime';

import { SettingsService } from './settings.service';

import { SettingsRoleModalComponent } from './settings.roles.modal.component';

import { Role } from '../models/role';
import { AvailableResourceAction } from '../models/availableResourceAction';
import { GenericObject } from '../models/genericObject';

@Component({
	selector: 'settings-roles-component',
	templateUrl: 'client/settings/settings.roles.html',
	styleUrls: [
		'client/settings/settings.css',
	],
	encapsulation: ViewEncapsulation.None,
	providers: [SettingsService],
})
export class SettingsRolesComponent {
	availableResourceActions: AvailableResourceAction[] = [];
	//Role Data Table params
	roles: Role[] = [];
	displayRoles: Role[] = [];
	filterQuery: FormControl = new FormControl();

	constructor(
		private settingsService: SettingsService, private modalService: NgbModal,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {
		this.toastyConfig.theme = 'bootstrap';

		this.getAvailableResourceActions();
		this.getRoles();

		this.filterQuery
			.valueChanges
			.debounceTime(500)
			.subscribe(event => this.filterRoles());
	}

	filterRoles() {
		const searchFilter = this.filterQuery.value ? this.filterQuery.value.toLocaleLowerCase() : '';

		this.displayRoles = this.roles.filter((user) => {
			return user.name.toLocaleLowerCase().includes(searchFilter);
		});
	}

	getAvailableResourceActions(): void {
		this.settingsService
			.getAvailableResourceActions()
			.then(availableResourceActions => this.availableResourceActions = availableResourceActions)
			.catch(e => this.toastyService.error(e.message));
	}

	getRoles(): void {
		this.settingsService
			.getRoles()
			.then(roles => this.displayRoles = this.roles = roles)
			.catch(e => this.toastyService.error(e.message));
	}

	addRole(): void {
		const modalRef = this.modalService.open(SettingsRoleModalComponent);
		modalRef.componentInstance.title = 'Add New Role';
		modalRef.componentInstance.submitText = 'Add Role';
		modalRef.componentInstance.availableResourceActions = this.availableResourceActions;
		modalRef.componentInstance.workingRole = new Role();

		this._handleModalClose(modalRef);
	}

	editRole(role: Role): void {
		const modalRef = this.modalService.open(SettingsRoleModalComponent);
		modalRef.componentInstance.title = `Edit Role: ${role.name}`;
		modalRef.componentInstance.submitText = 'Save Changes';
		modalRef.componentInstance.availableResourceActions = this.availableResourceActions;
		modalRef.componentInstance.workingRole = _.cloneDeep(role);

		this._handleModalClose(modalRef);
	}

	deleteRole(roleToDelete: Role): void {
		if (!confirm(`Are you sure you want to delete the role "${roleToDelete.name}"?`)) { return; }

		this.settingsService
			.deleteRole(roleToDelete.id)
			.then(() => {
				this.roles = this.roles.filter(role => role.id !== roleToDelete.id);

				this.filterRoles();

				this.toastyService.success(`Role "${roleToDelete.name}" successfully deleted.`);
			})
			.catch(e => this.toastyService.error(e.message));
	}

	getFriendlyPermissions(role: Role): string {
		const obj = role.resources.reduce((accumulator: GenericObject, resource) => {
			let key = resource.name;
			if (resource.app_name) { key += ` - ${resource.app_name}`; }

			accumulator[key] = resource.permissions;
			return accumulator;
		}, {});

		let out = JSON.stringify(obj, null, 1);
		out = out.replace(/[\{\}"]/g, '').trim();
		return out;
	}

	private _handleModalClose(modalRef: NgbModalRef): void {
		modalRef.result
			.then((result) => {
				//Handle modal dismiss
				if (!result || !result.role) { return; }

				//On edit, find and update the edited item
				if (result.isEdit) {
					const toUpdate = this.roles.find(r => r.id === result.role.id);
					Object.assign(toUpdate, result.role);

					this.filterRoles();

					this.toastyService.success(`Role "${result.role.name}" successfully edited.`);
				} else {
					this.roles.push(result.role);

					this.filterRoles();

					this.toastyService.success(`Role "${result.role.name}" successfully added.`);
				}
			},
			(error) => { if (error) { this.toastyService.error(error.message); } });
	}
}
