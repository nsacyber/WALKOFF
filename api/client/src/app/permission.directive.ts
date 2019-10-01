import {
    Directive,
    Input,
    TemplateRef,
    ViewContainerRef,
    OnInit,
} from '@angular/core';
import { PermissionService } from './permission.service';

/* 
*  Based on: https://stackblitz.com/edit/angular-permission-directive
*  Usage <div *hasPermission="['isAdmin]"> {{ Protected  }}</div>
*
*  Setting all to true performs an AND operation on passed permissions requiring them all
*  IE: <div *hasPermission="['viewReports', 'editReports'] all:true"> {{ Protected  }}</div>
*/
@Directive({
    selector: '[hasPermission]'
})
export class HasPermissionDirective implements OnInit {
    private permissions = [];
    private matchAll = false;
    private isHidden = true;

    constructor(
        private templateRef: TemplateRef<any>, private viewContainer: ViewContainerRef, 
        private permissionService: PermissionService
    ) {}

    ngOnInit() { }

    @Input()
    set hasPermission(val) {
        this.permissions = Array.isArray(val) ? val : [ val ];
        this.updateView();
    }

    @Input()
    set hasPermissionAll(matchAll: boolean) {
        this.matchAll = matchAll;
        this.updateView();
    }

    private async updateView() {
        if (await this.checkPermission()) {
            if (this.isHidden) {
                this.viewContainer.createEmbeddedView(this.templateRef);
                this.isHidden = false;
            }
        } else {
            this.isHidden = true;
            this.viewContainer.clear();
        }
    }

    private async checkPermission() {
        const results = await Promise.all(this.permissions.map(p => this.permissionService.checkPermission(p)));
        return (this.matchAll) ? results.every(r => r == true) : results.some(r => r == true)
    }
}