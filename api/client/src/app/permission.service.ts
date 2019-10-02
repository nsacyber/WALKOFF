import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { plainToClass } from 'class-transformer';
import { UtilitiesService } from './utilities.service';
import { timer } from 'rxjs';
import { takeWhile } from 'rxjs/operators';
import { Role } from './models/role';

@Injectable({
    providedIn: 'root'
})
export class PermissionService {
    permissionsLoaded = false;
    fetchedPermissions;

    permissions = {
        isUser: [
            { resource: 'app_apis', permissions: ["read"] },
            { resource: 'dashboards', permissions: ["read"] },
            { resource: 'global_variables', permissions: ["read"] },
            { resource: 'workflows', permissions: ["read"] },
            { resource: 'workflowstatus', permissions: ["read"] },
            { resource: 'workflow_variables', permissions: ["read", "update"] },
        ],
        isAdmin: [
            { resource: 'app_apis', permissions: ["create", "read", "update", "delete"] },
            { resource: 'apps', permissions: ["create", "read", "update", "delete"] },
            { resource: 'dashboards', permissions: ["create", "read", "update", "delete"] },
            { resource: 'global_variables', permissions: ["create", "read", "update", "delete"] },
            { resource: 'roles', permissions: ["create", "read", "update", "delete"] },
            { resource: 'scheduler', permissions: ["create", "read", "update", "delete", "execute"] },
            { resource: 'settings', permissions: ["read", "update"] },
            { resource: 'users', permissions: ["create", "read", "update", "delete"] },
            { resource: 'workflows', permissions: ["create", "read", "update", "delete", "execute"] },
            { resource: 'workflowstatus', permissions: ["create", "read", "update", "delete"] },
            { resource: 'workflow_variables', permissions: ["create", "read", "update", "delete"] },
        ],
        executeWorkflows: [
            { resource: 'app_apis', permissions: ["read"] },
            { resource: 'workflows', permissions: ["read", "execute"] },
            { resource: 'workflow_variables', permissions: ["read"] },
        ],
        editWorkflows: [
            { resource: 'app_apis', permissions: ["read"] },
            { resource: 'global_variables', permissions: ["read"] },
            { resource: 'workflows', permissions: ["create", "read", "update", "delete", "execute"] },
            { resource: 'workflowstatus', permissions: ["read"] },
            { resource: 'workflow_variables', permissions: ["create", "read", "update", "delete"] },
        ],
        viewReports: [
            { resource: 'dashboards', permissions: ["read"] },
            { resource: 'workflows', permissions: ["read"] },
            { resource: 'workflowstatus', permissions: ["read"] },
        ],
        editReports: [
            { resource: 'dashboards', permissions: ["create", "read", "update", "delete"] },
            { resource: 'workflows', permissions: ["read"] },
            { resource: 'workflowstatus', permissions: ["read"] },
        ],
        editApps: [
            { resource: 'app_apis', permissions: ["read"] },
            { resource: 'apps', permissions: ["create", "read", "update", "delete"] },
        ],
        editSchedule: [
            { resource: 'workflows', permissions: ["read"] },
            { resource: 'scheduler', permissions: ["create", "read", "update", "delete", "execute"] },
        ],
        editGlobals: [
            { resource: 'global_variables', permissions: ["create", "update", "delete"] },
        ],
    }
    
    constructor(private http: HttpClient, private utils: UtilitiesService) {
        // Refresh permissions every 30 seconds
        timer(0, 30000).subscribe(async _ => {
            this.fetchedPermissions = await this.fetchPermissions();
            this.permissionsLoaded = true;
        })
    }

    /**
	 * Asynchronously returns an array of existing globals from the server.
	 */
    private fetchPermissions(): Promise<any> {
        // Data manipulation functions to aggregate all role permissions to user has
        const flatten = (acc, cur) => [...acc, ...cur];
        const combine = (acc, cur, i, src) => {
            if (acc.find(r => r.name == cur.name)) return acc;
            cur.permissions = [... new Set(src.filter(s => s.name == cur.name).map(s => s.permissions).reduce(flatten))];
            return [...acc, cur];
        }

        return this.http.get(`api/users/permissions/`)
            .toPromise()
            .then((data: any) => plainToClass(Role, data as any[]))
            .then((roles) => roles.map(r => r.resources).reduce(flatten).reduce(combine, []))
            .then((permissions) => this.fetchedPermissions = permissions)
            .catch(this.utils.handleResponseError);
    }

	/**
	 * Asynchronously returns an array of existing globals from the server.
	 */
    async getPermissions() {
        await this.waitUntilReady();
        return this.fetchedPermissions ? this.fetchedPermissions : this.fetchPermissions();
    }

    async checkPermission(permission: string): Promise<boolean> {
        const actionResources = this.permissions[permission];
        if (!actionResources) throw(`${permission} is an invalid permission.`)

        const userResources = await this.getPermissions();
        return actionResources.every(ar => {
            const ur = userResources.find(ur => ur.name == ar.resource);
            return ur && ar.permissions.every(p => ur.permissions.includes(p));
        });
    }

    waitUntilReady() {
        return timer(0, 100).pipe(takeWhile(_ => !this.permissionsLoaded, true)).last().toPromise();
    }
}
