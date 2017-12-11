import { Component, Input } from '@angular/core';
import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { ToastyService, ToastyConfig } from 'ng2-toasty';
import { Select2OptionData } from 'ng2-select2';

import { SettingsService } from './settings.service';

import { Role } from '../models/role';
import { AvailableResourceAction } from '../models/availableResourceAction';
import { Resource } from '../models/resource';

@Component({
	selector: 'settings-role-modal',
	templateUrl: 'client/settings/settings.roles.modal.html',
	styleUrls: [
		'client/settings/settings.css',
	],
	providers: [SettingsService],
})
export class SettingsRoleModalComponent {
	@Input() workingRole: Role;
	@Input() title: string;
	@Input() submitText: string;
	@Input() availableResourceActions: AvailableResourceAction[];

	typeNames: string[] = [];
	selectPermissionMapping: { [key: string]: Select2OptionData[] } = {};
	permissionSelectConfig: Select2Options;
	newResourceTempIdTracker: number = -1;
	selectedAvailableResourceActionName: string;

	constructor(
		private settingsService: SettingsService, private activeModal: NgbActiveModal,
		private toastyService: ToastyService, private toastyConfig: ToastyConfig,
	) {
		this.toastyConfig.theme = 'bootstrap';

		this.permissionSelectConfig = {
			width: '100%',
			placeholder: 'Select permission(s) for this resource',
			multiple: true,
			allowClear: true,
			closeOnSelect: false,
		};
	}

	ngOnInit(): void {
		this.availableResourceActions.forEach(ara => {
			let typeName = ara.name;

			if (ara.app_name) { typeName += ` - ${ara.app_name}`; }

			this.typeNames.push(typeName);
		});

		// On init, set up our select2 stuff first
		this.workingRole.resources.forEach(resource => {
			const matchingAvailableResourceAction = this.availableResourceActions
				.find(a => a.name === resource.name && a.app_name === resource.app_name);
			this.selectPermissionMapping[resource.resource_id] = matchingAvailableResourceAction.actions.map(action => {
				return {
					id: action,
					text: action,
				};
			});
		});
	}

	addResource(): void {
		const selectedAvailableResourceAction = this.availableResourceActions.find(a => {
			const selectedInfo = this.selectedAvailableResourceActionName.split(' - ');
			if (selectedInfo.length === 1) { return a.name === selectedInfo[0]; }
			return a.name === selectedInfo[0] && a.app_name === selectedInfo[1];
		});

		const newResource: Resource = {
			resource_id: this.newResourceTempIdTracker--,
			role_id: this.workingRole.id,
			name: selectedAvailableResourceAction.name,
			permissions: [],
		};

		if (selectedAvailableResourceAction.app_name) { newResource.app_name = selectedAvailableResourceAction.app_name; }

		this.selectPermissionMapping[newResource.resource_id] = selectedAvailableResourceAction.actions.map(action => {
			return {
				id: action,
				text: action,
			};
		});

		this.workingRole.resources.push(newResource);
	}

	removeResource(resource: Resource): void {
		this.workingRole.resources.splice(this.workingRole.resources.indexOf(resource), 1);
	}

	permissionSelectChange(event: any, resource: Resource) {
		resource.permissions = event.value;
	}

	submit(): void {
		const validationMessage = this.validate();
		if (validationMessage) {
			this.toastyService.error(validationMessage);
			return;
		}

		// Remove temp Ids for new resources
		this.workingRole.resources.forEach(resource => {
			if (resource.resource_id < 0) { delete resource.resource_id; }
		});

		//If role has an ID, it already exists, call update
		if (this.workingRole.id) {
			this.settingsService
				.editRole(this.workingRole)
				.then(role => this.activeModal.close({
					role,
					isEdit: true,
				}))
				.catch(e => this.toastyService.error(e.message));
		} else {
			this.settingsService
				.addRole(this.workingRole)
				.then(role => this.activeModal.close({
					role,
					isEdit: false,
				}))
				.catch(e => this.toastyService.error(e.message));
		}
	}

	validate(): string {
		return '';
	}
}
