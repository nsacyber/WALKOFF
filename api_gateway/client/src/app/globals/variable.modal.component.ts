import { Component, Input, OnInit } from '@angular/core';

import { NgbActiveModal } from '@ng-bootstrap/ng-bootstrap';
import { Variable, VariablePermission } from '../models/variable';
import { SettingsService } from '../settings/settings.service';
import { Role } from '../models/role';
import { ToastrService } from 'ngx-toastr';

@Component({
    selector: 'variable-modal-component',
    templateUrl: './variable.modal.html',
    styleUrls: [
        './variable.modal.scss',
    ],
})
export class VariableModalComponent implements OnInit {
    @Input() variable: Variable = new Variable();
    @Input() isGlobal: boolean = false;
    existing: boolean = false;
    hasPermissions: boolean = true;
    permissionOptions = VariablePermission.PERMISSIONS;
    systemRoles: Role[];
    permissions: any[] = [];
    newPermission: any = { role: '', permissions: '' };

    constructor(public activeModal: NgbActiveModal, public settingsService: SettingsService, public toastrService: ToastrService) { }

    ngOnInit(): void {
        this.settingsService.getRoles().then(roles => this.systemRoles = roles);
    }

    addPermission() {
        if (!this.getRoleName(this.newPermission) || !this.getPermissionDescription(this.newPermission)) {
            return this.toastrService.error('Select a role and permission');
        }

        const existingPermission = this.variable.permissions.find(p => p.role == this.newPermission.role);
        (existingPermission) ? 
            existingPermission.permissions = this.newPermission.permissions : 
            this.variable.permissions.push(this.newPermission);
        
        this.variable.permissions.sort((a, b) => a.role.localeCompare(b.role));
        this.newPermission = { role: '', permissions: '' };
    }

    deletePermission(p: any) {
        this.variable.permissions = this.variable.permissions.filter(permission => permission.role != p.role);
    }

    getRoleName(p: any): string {
        const role = this.systemRoles.find(role => role.name == p.role);
        return role ? role.name : null;
    }

    getPermissionDescription(r: any): string {
        const permission = this.permissionOptions.find(o => JSON.stringify(o.crud) == JSON.stringify(r.permissions))
        return permission ? permission.description : null;
    }
}