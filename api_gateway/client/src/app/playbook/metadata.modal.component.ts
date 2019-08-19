import { Component, Input, ViewChild } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { Workflow, WorkflowPermission } from '../models/playbook/workflow';
import { NgForm, NgModel } from '@angular/forms';
import { Role } from '../models/role';
import { SettingsService } from '../settings/settings.service';
import { ToastrService } from 'ngx-toastr';

@Component({
    selector: 'metadata-modal-component',
    templateUrl: './metadata.modal.html',
    styleUrls: [
		'./metadata.modal.scss',
	],
})
export class MetadataModalComponent {
    @Input() workflow: Workflow = new Workflow();
    @Input() existingWorkflows: Workflow[] = [];
    @Input() currentTags: string[] = [];
    @Input() existing: boolean = false;

    permissionOptions = WorkflowPermission.PERMISSIONS;
    systemRoles: Role[] = [];
    newPermission: any = { role: '', permissions: '' };

    @ViewChild('myForm', { static: true })
    myForm: NgForm;

    @ViewChild('workflowName', { static: true }) 
    workflowNameModel: NgModel;

    tagSelectOptions = {
        multiple: true,
        tags: true,
        width: '100%',
        placeholder: 'Add Tags...'
    };

    constructor(public activeModal: NgbActiveModal, public settingsService: SettingsService, public toastrService: ToastrService) { }

    ngOnInit(): void {
        this.settingsService.getRoles().then(roles => this.systemRoles = roles);
    }

    tagsChanged($event: any): void {
		this.workflow.tags = $event.value;
    }
    
    submit() {
        const compareWorkflow = (w: Workflow) => 
            w.name.toLocaleLowerCase() == this.workflow.name.toLocaleLowerCase() && w.id != this.workflow.id;

        if (!this.workflow.name) {
            this.workflowNameModel.control.setErrors({'required': true});
        }
        else if (this.existingWorkflows.find(compareWorkflow)) {
            this.workflowNameModel.control.setErrors({'unique': true});
        }

        if (this.myForm.valid) this.activeModal.close(this.workflow);
    }

    addPermission() {
        if (!this.getRoleName(this.newPermission) || !this.getPermissionDescription(this.newPermission)) {
            return this.toastrService.error('Select a role and permission');
        }

        const existingPermission = this.workflow.permissions.find(p => p.role == this.newPermission.role);
        (existingPermission) ? 
            existingPermission.permissions = this.newPermission.permissions : 
            this.workflow.permissions.push(this.newPermission);
        
        this.workflow.permissions.sort((a, b) => this.getRoleName(a).localeCompare(this.getRoleName(b)));
        this.newPermission = { role: '', permissions: '' };
    }

    deletePermission(p: any) {
        this.workflow.permissions = this.workflow.permissions.filter(permission => permission.role != p.role);
    }

    getRoleName(p: any): string {
        const role = this.systemRoles.find(role => role.id == p.role);
        return role ? role.name : null;
    }

    getPermissionDescription(r: any): string {
        const permission = this.permissionOptions.find(o => JSON.stringify(o.crud) == JSON.stringify(r.permissions))
        return permission ? permission.description : null;
    }
}