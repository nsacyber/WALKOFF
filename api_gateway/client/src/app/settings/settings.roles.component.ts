import { Component, ViewEncapsulation } from '@angular/core';
import { FormControl } from '@angular/forms';
import { NgbModal, NgbModalRef } from '@ng-bootstrap/ng-bootstrap';
import { ToastrService } from 'ngx-toastr';
import 'rxjs/add/operator/debounceTime';

import { SettingsService } from './settings.service';
import { UtilitiesService } from '../utilities.service';

import { SettingsRoleModalComponent } from './settings.roles.modal.component';

import { Role } from '../models/role';
import { AvailableResourceAction } from '../models/availableResourceAction';
import { GenericObject } from '../models/genericObject';

@Component({
	selector: 'settings-roles-component',
	templateUrl: './settings.roles.html',
	styleUrls: [
		'./settings.scss',
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
		private toastrService: ToastrService, private utils: UtilitiesService,
	) {

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
			.catch(e => this.toastrService.error(e.message));
	}

	getRoles(): void {
		this.settingsService
			.getRoles()
			.then(roles => this.displayRoles = this.roles = roles)
			.catch(e => this.toastrService.error(e.message));
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
		modalRef.componentInstance.workingRole = this.utils.cloneDeep(role);

		this._handleModalClose(modalRef);
	}

	async deleteRole(roleToDelete: Role) {
		await this.utils.confirm(`Are you sure you want to delete <b>${roleToDelete.name}</b>?`)

		this.settingsService
			.deleteRole(roleToDelete.id)
			.then(() => {
				this.roles = this.roles.filter(role => role.id !== roleToDelete.id);

				this.filterRoles();

				this.toastrService.success(`Role "${roleToDelete.name}" successfully deleted.`);
			})
			.catch(e => this.toastrService.error(e.message));
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

					this.toastrService.success(`Role "${result.role.name}" successfully edited.`);
				} else {
					this.roles.push(result.role);

					this.filterRoles();

					this.toastrService.success(`Role "${result.role.name}" successfully added.`);
				}
			},
			(error) => { if (error) { this.toastrService.error(error.message); } });
	}
}
